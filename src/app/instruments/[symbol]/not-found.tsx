import Link from "next/link";

export default function InstrumentNotFound() {
  return (
    <main className="page-shell stock-page">
      <h1>Instrument not found</h1>
      <p>No validated fixture exists for this symbol.</p>
      <Link href="/">Return home</Link>
    </main>
  );
}
