import { useState } from "react";
import StockChart from "./Stockchart";

function Prediction() {
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchHistory, setSearchHistory] = useState<string[]>(() => {
  try {
    return JSON.parse(
      localStorage.getItem("stockpulse_search_history") || "[]"
    );
  } catch {
    return [];
  }
});

  const getPrediction = async () => {
    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/predict?ticker=${encodeURIComponent(ticker)}&mode=binary`
      );

      if (!response.ok) {
        throw new Error("Unable to fetch prediction.");
      }

      const result = await response.json();
      setData(result);
      const searchedTicker = ticker.trim().toUpperCase();

const updatedHistory = [
  searchedTicker,
  ...searchHistory.filter((item) => item !== searchedTicker),
].slice(0, 5);

setSearchHistory(updatedHistory);

localStorage.setItem(
  "stockpulse_search_history",
  JSON.stringify(updatedHistory)
);
    } catch {
      setError("Backend connection failed. Check whether API is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 p-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">
        StockPulse Prediction
      </h1>

      <div className="mb-6 flex gap-3">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter stock ticker"
          className="rounded-lg border border-slate-600 bg-slate-800 p-3"
        />

        <button
          onClick={getPrediction}
          disabled={loading || !ticker.trim()}
          className="rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-700"
        >
          {loading ? "Loading..." : "Predict"}
        </button>
      </div>
      {searchHistory.length > 0 && (
  <div className="mb-6 rounded-xl bg-slate-800 p-4">
    <h2 className="mb-3 text-lg font-semibold">
      Recent Searches
    </h2>

    <div className="flex flex-wrap gap-2">
      {searchHistory.map((stock) => (
        <button
          key={stock}
          onClick={() => setTicker(stock)}
          className="rounded-lg bg-slate-700 px-4 py-2 hover:bg-blue-600"
        >
          {stock}
        </button>
      ))}
    </div>
  </div>
)}

      {error && <p className="text-red-400">{error}</p>}

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-slate-800 p-5">
              <h2 className="text-xl font-semibold">Prediction</h2>
              <p className="mt-3 text-3xl font-bold">
                {data.prediction.trend}
              </p>
              <p>
                Confidence: {(data.prediction.confidence * 100).toFixed(2)}%
              </p>
              <p>
                Latest Close: {data.currency}{data.latest_close}
              </p>
            </div>

            <div className="rounded-xl bg-slate-800 p-5">
              <h2 className="text-xl font-semibold">Risk Analysis</h2>
              <p>Risk Level: {data.risk_factors.risk_level}</p>
              <p>Risk Score: {data.risk_factors.risk_score}</p>
              <p>RSI: {data.technical_analysis.rsi}</p>
            </div>

            <div className="rounded-xl bg-slate-800 p-5">
              <h2 className="text-xl font-semibold">
                Support & Resistance
              </h2>
              <p>Support: {data.technical_analysis.support}</p>
              <p>Resistance: {data.technical_analysis.resistance}</p>
            </div>
          </div>

          <StockChart
            history={data.chart_history}
            currency={data.currency}
          />
        </>
      )}
    </div>
  );
}

export default Prediction;

