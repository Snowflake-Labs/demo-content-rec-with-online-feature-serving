import { querySnowflake } from "@/lib/snowflake"
import { NextRequest } from "next/server"

export const dynamic = "force-dynamic"

const CATEGORY_MAP: Record<number, string> = {
  0: "Books",
  1: "Clothing",
  2: "Electronics",
  3: "Home",
  4: "Sports",
}
const PRICE_MAP: Record<number, string> = { 0: "High", 1: "Low", 2: "Medium" }

export async function POST(req: NextRequest) {
  try {
    const { userId } = await req.json()
    if (!userId) {
      return Response.json({ error: "userId is required" }, { status: 400 })
    }

    // Sample 10 random candidate items from the ITEMS table
    const itemRows = await querySnowflake(`
      SELECT
        ITEM_ID,
        CATEGORY,
        PRICE_RANGE,
        AVG_RATING,
        CASE CATEGORY
          WHEN 'Books'       THEN 0 WHEN 'Clothing'     THEN 1
          WHEN 'Electronics' THEN 2 WHEN 'Home'          THEN 3
          WHEN 'Sports'      THEN 4 ELSE 0
        END AS ITEM_CATEGORY_ENC,
        CASE PRICE_RANGE
          WHEN 'High' THEN 0 WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 ELSE 0
        END AS PRICE_RANGE_ENC
      FROM RECOMMEND_DB.RECOMMEND.ITEMS
      ORDER BY RANDOM()
      LIMIT 10
    `)

    if (!itemRows.length) {
      return Response.json({ error: "No items found" }, { status: 404 })
    }

    // Resolve internal inference endpoint from SPCS env variable or env
    const internalEndpoint =
      process.env.INFERENCE_INTERNAL_ENDPOINT ||
      process.env.NEXT_PUBLIC_INFERENCE_ENDPOINT ||
      ""

    if (!internalEndpoint) {
      return Response.json(
        { error: "INFERENCE_INTERNAL_ENDPOINT is not set" },
        { status: 500 }
      )
    }

    // Build request: USER_ID triggers Feature Store lookup for user features;
    // item features are passed directly (max 1 Feature View per function)
    const data = itemRows.map((item) => [
      userId,
      item.ITEM_CATEGORY_ENC,
      item.PRICE_RANGE_ENC,
      item.AVG_RATING,
    ])

    const payload = {
      dataframe_split: {
        index: itemRows.map((_, i) => i),
        columns: ["USER_ID", "ITEM_CATEGORY_ENC", "PRICE_RANGE_ENC", "AVG_RATING"],
        data,
      },
    }

    // Use SPCS service token for auth (no PAT required)
    let token = ""
    try {
      const fs = await import("fs")
      token = fs.readFileSync("/snowflake/session/token", "utf8").trim()
    } catch {
      // Local dev fallback
      token = process.env.SNOWFLAKE_PAT || ""
    }

    const inferenceRes = await fetch(
      `${internalEndpoint.replace(/\/$/, "")}/predict-proba`,
      {
        method: "POST",
        headers: {
          Authorization: `Snowflake Token="${token}"`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    )

    if (!inferenceRes.ok) {
      const text = await inferenceRes.text()
      return Response.json(
        { error: `Inference service error: ${inferenceRes.status} ${text}` },
        { status: 502 }
      )
    }

    const result = await inferenceRes.json()
    const scores: number[][] = result.predictions ?? []

    // Rank by click probability (index 1 = probability of click)
    const ranked = itemRows
      .map((item, i) => ({
        item_id: item.ITEM_ID,
        category: item.CATEGORY,
        price_range: item.PRICE_RANGE,
        avg_rating: item.AVG_RATING,
        click_score: scores[i]?.[1] ?? 0,
      }))
      .sort((a, b) => b.click_score - a.click_score)

    return Response.json({ userId, items: ranked })
  } catch (e) {
    console.error(new Date().toISOString(), "[recommend]", e)
    return Response.json(
      { error: e instanceof Error ? e.message : "Recommendation failed" },
      { status: 500 }
    )
  }
}
