import { useState } from "react";
import Prediction from "./components/Prediction";
import { Report } from "./components/RiskPulse/Report";

function App() {
const [activeTab, setActiveTab] = useState("prediction");

return (
<div className="min-h-screen bg-slate-950 text-white">
<nav className="sticky top-0 z-50 flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 bg-slate-900 px-6 py-4">
<h1 className="text-xl font-bold">StockPulse</h1>

    <div className="flex gap-2">
      <button
        onClick={() => setActiveTab("prediction")}
        className={`rounded-lg px-4 py-2 font-semibold ${
          activeTab === "prediction"
            ? "bg-blue-600 text-white"
            : "bg-slate-700 text-slate-300"
        }`}
      >
        Prediction
      </button>

      <button
        onClick={() => setActiveTab("research")}
        className={`rounded-lg px-4 py-2 font-semibold ${
          activeTab === "research"
            ? "bg-blue-600 text-white"
            : "bg-slate-700 text-slate-300"
        }`}
      >
        Research & Reports
      </button>
    </div>
  </nav>

  <main className="p-4 md:p-8">
    {activeTab === "prediction" ? <Prediction /> : <Report />}
  </main>
</div>

);
}

export default App;