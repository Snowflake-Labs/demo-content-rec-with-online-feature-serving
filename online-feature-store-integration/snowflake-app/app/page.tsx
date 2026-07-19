"use client"

import { useState } from "react"

interface UserFeatures {
  USER_ID: string
  PURCHASE_COUNT_30D: number
  CLICK_RATE_7D: number
  PREFERRED_CATEGORY_LABEL: string
}

interface RecommendedItem {
  item_id: string
  category: string
  price_range: string
  avg_rating: number
  click_score: number
}

const CATEGORY_EMOJI: Record<string, string> = {
  Electronics: "💻",
  Clothing: "👕",
  Books: "📚",
  Sports: "⚽",
  Home: "🏠",
}

export default function RecommendPage() {
  const [userId, setUserId] = useState("user_0042")
  const [userFeatures, setUserFeatures] = useState<UserFeatures | null>(null)
  const [items, setItems] = useState<RecommendedItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function getRecommendations() {
    if (!userId.trim()) return
    setLoading(true)
    setError(null)
    setUserFeatures(null)
    setItems([])

    try {
      // Fetch user features from Feature Store (for display)
      const featRes = await fetch(
        `/api/user-features?userId=${encodeURIComponent(userId)}`
      )
      const featData = await featRes.json()
      if (featRes.ok) setUserFeatures(featData)

      // Fetch recommendations (inference service auto-fetches user features)
      const recRes = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId }),
      })
      const recData = await recRes.json()
      if (!recRes.ok) throw new Error(recData.error ?? "Recommendation failed")
      setItems(recData.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-3xl mx-auto py-10 px-4 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Product Recommendations
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Powered by Snowflake Online Feature Store + SPCS Inference
        </p>
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && getRecommendations()}
          placeholder="e.g. user_0042"
          className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={getRecommendations}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {loading ? "Loading…" : "Get Recommendations"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* User features panel */}
      {userFeatures && (
        <div className="rounded-lg border bg-muted/40 p-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">
            User Features (fetched from Online Feature Store)
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <FeatureTile
              label="Purchases (30d)"
              value={String(userFeatures.PURCHASE_COUNT_30D)}
            />
            <FeatureTile
              label="Click Rate (7d)"
              value={`${(userFeatures.CLICK_RATE_7D * 100).toFixed(1)}%`}
            />
            <FeatureTile
              label="Preferred Category"
              value={userFeatures.PREFERRED_CATEGORY_LABEL}
            />
            <FeatureTile label="User ID" value={userFeatures.USER_ID} />
          </div>
          <p className="text-xs text-muted-foreground mt-3 italic">
            These features were automatically retrieved by the inference service
            via <code className="font-mono">feature_sources_per_function</code> —
            only USER_ID was sent in the request.
          </p>
        </div>
      )}

      {/* Results */}
      {items.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-3">
            Top {items.length} recommended items for{" "}
            <span className="font-mono">{userId}</span>
          </p>
          <div className="space-y-2">
            {items.map((item, i) => (
              <div
                key={item.item_id}
                className="flex items-center gap-4 border rounded-lg px-4 py-3 bg-card"
              >
                <span className="text-muted-foreground text-sm w-5 text-right">
                  {i + 1}
                </span>
                <span className="text-xl">
                  {CATEGORY_EMOJI[item.category] ?? "🛍️"}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{item.item_id}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.category} · {item.price_range} · ★{" "}
                    {item.avg_rating.toFixed(1)}
                  </p>
                </div>
                <ScoreBar score={item.click_score} />
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  )
}

function FeatureTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-background border px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold mt-0.5 truncate">{value}</p>
    </div>
  )
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 70
      ? "bg-emerald-500"
      : pct >= 40
        ? "bg-amber-400"
        : "bg-slate-300"
  return (
    <div className="flex items-center gap-2 w-28 shrink-0">
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-muted-foreground w-9 text-right">
        {pct}%
      </span>
    </div>
  )
}
