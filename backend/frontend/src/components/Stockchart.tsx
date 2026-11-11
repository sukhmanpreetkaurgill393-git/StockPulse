import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
} from "lightweight-charts";

type StockRecord = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type Props = {
  history: StockRecord[];
  currency?: string;
};

function StockChart({ history, currency = "$" }: Props) {
  const candleRef = useRef<HTMLDivElement>(null);
  const lineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!history?.length || !candleRef.current || !lineRef.current) {
      return;
    }

    const candleChart = createChart(candleRef.current, {
      height: 320,
      layout: {
        background: { color: "#0f172a" },
        textColor: "#cbd5e1",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: true,
      },
    });

    const candles = candleChart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    candles.setData(
      history.map((item) => ({
        time: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }))
    );

    const lineChart = createChart(lineRef.current, {
      height: 280,
      layout: {
        background: { color: "#0f172a" },
        textColor: "#cbd5e1",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
      timeScale: {
        borderColor: "#334155",
      },
    });

    const line = lineChart.addSeries(LineSeries, {
      color: "#38bdf8",
      lineWidth: 2,
    });

    line.setData(
      history.map((item) => ({
        time: item.date,
        value: item.close,
      }))
    );

    candleChart.timeScale().fitContent();
    lineChart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      if (candleRef.current && lineRef.current) {
        candleChart.applyOptions({
          width: candleRef.current.clientWidth,
        });

        lineChart.applyOptions({
          width: lineRef.current.clientWidth,
        });
      }
    });

    resizeObserver.observe(candleRef.current);
    resizeObserver.observe(lineRef.current);

    return () => {
      resizeObserver.disconnect();
      candleChart.remove();
      lineChart.remove();
    };
  }, [history]);

  return (
    <div className="mt-8 space-y-6">
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <h2 className="mb-2 text-xl font-bold text-white">
          Candlestick Chart
        </h2>
        <p className="mb-4 text-sm text-slate-400">
          Open, High, Low and Close prices
        </p>
        <div ref={candleRef} className="w-full" />
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <h2 className="mb-2 text-xl font-bold text-white">
          Price History
        </h2>
        <p className="mb-4 text-sm text-slate-400">
          Closing price movement · {currency}
        </p>
        <div ref={lineRef} className="w-full" />
      </div>
    </div>
  );
}

export default StockChart;