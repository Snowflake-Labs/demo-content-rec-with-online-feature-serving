import { querySnowflake } from "@/lib/snowflake"
import { NextRequest } from "next/server"

export const dynamic = "force-dynamic"

export async function GET(req: NextRequest) {
  try {
    const userId = req.nextUrl.searchParams.get("userId")
    if (!userId) {
      return Response.json({ error: "userId is required" }, { status: 400 })
    }

    const rows = await querySnowflake(`
      SELECT
        USER_ID,
        PURCHASE_COUNT_30D,
        ROUND(CLICK_RATE_7D, 3)   AS CLICK_RATE_7D,
        PREFERRED_CATEGORY_ENC,
        CASE PREFERRED_CATEGORY_ENC
          WHEN 0 THEN 'Books'       WHEN 1 THEN 'Clothing'
          WHEN 2 THEN 'Electronics' WHEN 3 THEN 'Home'
          WHEN 4 THEN 'Sports'      ELSE 'Unknown'
        END AS PREFERRED_CATEGORY_LABEL
      FROM RECOMMEND_DB.RECOMMEND.USER_FEATURES_V
      WHERE USER_ID = '${userId.replace(/'/g, "''")}'
      LIMIT 1
    `)

    if (!rows.length) {
      return Response.json({ error: "User not found" }, { status: 404 })
    }

    return Response.json(rows[0])
  } catch (e) {
    console.error(new Date().toISOString(), "[user-features]", e)
    return Response.json(
      { error: e instanceof Error ? e.message : "Failed to fetch user features" },
      { status: 500 }
    )
  }
}
