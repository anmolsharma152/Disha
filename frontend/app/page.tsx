export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <main className="flex flex-col items-center gap-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Disha
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-md">
          Market Intelligence & Career Optimization for India&apos;s AI/ML landscape.
        </p>
        <div className="flex gap-3 text-sm text-gray-500 dark:text-gray-500">
          <span>Agentic Orchestration</span>
          <span aria-hidden="true">·</span>
          <span>Greenhouse Ingestion</span>
          <span aria-hidden="true">·</span>
          <span>Career Matching</span>
        </div>
      </main>
    </div>
  );
}
