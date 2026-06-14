/**
 * DigiViCHI Nexus Shell — Local Service Watchdog / Fallback Detector
 *
 * Purpose:
 * - Detect when local/off-grid services are ONLINE, DEGRADED, OFFLINE, or UNKNOWN.
 * - Emit fallback ProposalRecords instead of executing recovery actions.
 * - Keep output compact by default for token-efficient AI handoff.
 *
 * Safety:
 * - No shell execution.
 * - No Docker control.
 * - No filesystem writes unless --out is explicitly provided.
 * - No live remediation.
 * - All recovery actions are ProposalRecords only.
 *
 * Runtime:
 * - Node 18+ recommended for global fetch and AbortSignal.timeout.
 * - Works with `tsx scripts/service-watchdog.ts --config config/service-registry.json`.
 */

import { promises as fs } from "node:fs";
import net from "node:net";
import process from "node:process";

export type ServiceState = "ONLINE" | "DEGRADED" | "OFFLINE" | "UNKNOWN";
export type CheckKind = "http" | "tcp";
export type AuthorityLabel =
  | "VIEW"
  | "DIAGNOSTIC_ONLY"
  | "PROPOSAL_ONLY"
  | "REQUIRES_AUDIT"
  | "LOCAL_FIRST"
  | "OFFGRID_READY";

export interface ServiceCheck {
  id: string;
  name: string;
  kind: CheckKind;
  url?: string;
  host?: string;
  port?: number;
  timeoutMs?: number;
  retries?: number;
  expectedStatus?: number[];
  critical?: boolean;
  fallback?: FallbackTarget[];
  tags?: string[];
}

export interface FallbackTarget {
  id: string;
  label: string;
  reason: string;
  mode: "mock" | "local" | "cached" | "degraded" | "manual";
  endpoint?: string;
  requiresApproval?: boolean;
}

export interface ServiceHealthRecord {
  id: string;
  name: string;
  state: ServiceState;
  latencyMs?: number;
  checkedAt: string;
  error?: string;
  attempts: number;
  critical: boolean;
  tags: string[];
  fallbackCandidates: FallbackTarget[];
}

export interface ProposalRecord {
  proposal_id: string;
  kind: "fallback_activation" | "service_review" | "manual_intervention";
  target: string;
  reason: string;
  risk: "LOW" | "MEDIUM" | "HIGH";
  authority: AuthorityLabel[];
  status: "DRAFT" | "STAGED";
  createdAt: string;
  fallback?: FallbackTarget;
}

export interface WatchdogReport {
  schema: "digivichi.service-watchdog.v0";
  mode: "LOCAL_FIRST";
  summary: {
    total: number;
    online: number;
    degraded: number;
    offline: number;
    unknown: number;
    criticalOffline: number;
    proposals: number;
  };
  services: ServiceHealthRecord[];
  proposals: ProposalRecord[];
  tokenBudget: {
    compactSummary: string;
    recommendedContext: "summary_only" | "summary_plus_failed_services" | "full_report";
  };
}

interface CliArgs {
  configPath: string;
  outPath?: string;
  full: boolean;
}

function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { configPath: "config/service-registry.json", full: false };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--config") args.configPath = argv[++i];
    else if (arg === "--out") args.outPath = argv[++i];
    else if (arg === "--full") args.full = true;
    else if (arg === "--help") {
      console.log("Usage: tsx scripts/service-watchdog.ts [--config path] [--out path] [--full]");
      process.exit(0);
    }
  }
  return args;
}

async function loadConfig(path: string): Promise<ServiceCheck[]> {
  const raw = await fs.readFile(path, "utf8");
  const parsed = JSON.parse(raw) as { services?: ServiceCheck[] } | ServiceCheck[];
  const services = Array.isArray(parsed) ? parsed : parsed.services;
  if (!services || !Array.isArray(services)) throw new Error("Config must contain an array of services.");
  return services;
}

async function checkHttp(service: ServiceCheck): Promise<{ ok: boolean; latencyMs: number; error?: string }> {
  if (!service.url) return { ok: false, latencyMs: 0, error: "Missing url" };
  const timeoutMs = service.timeoutMs ?? 1500;
  const expected = service.expectedStatus ?? [200, 204];
  const start = Date.now();
  try {
    const response = await fetch(service.url, {
      method: "GET",
      signal: AbortSignal.timeout(timeoutMs),
      headers: { "accept": "application/json,text/plain,*/*" }
    });
    const latencyMs = Date.now() - start;
    return { ok: expected.includes(response.status), latencyMs, error: expected.includes(response.status) ? undefined : `Unexpected HTTP ${response.status}` };
  } catch (err) {
    return { ok: false, latencyMs: Date.now() - start, error: err instanceof Error ? err.message : String(err) };
  }
}

function checkTcp(service: ServiceCheck): Promise<{ ok: boolean; latencyMs: number; error?: string }> {
  const host = service.host ?? "127.0.0.1";
  const port = service.port;
  const timeoutMs = service.timeoutMs ?? 1500;
  if (!port) return Promise.resolve({ ok: false, latencyMs: 0, error: "Missing port" });

  return new Promise((resolve) => {
    const start = Date.now();
    const socket = net.createConnection({ host, port });
    let settled = false;

    const finish = (ok: boolean, error?: string) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      resolve({ ok, latencyMs: Date.now() - start, error });
    };

    socket.setTimeout(timeoutMs);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false, `TCP timeout after ${timeoutMs}ms`));
    socket.once("error", (err) => finish(false, err.message));
  });
}

async function checkOnce(service: ServiceCheck): Promise<{ ok: boolean; latencyMs: number; error?: string }> {
  if (service.kind === "http") return checkHttp(service);
  if (service.kind === "tcp") return checkTcp(service);
  return { ok: false, latencyMs: 0, error: `Unsupported check kind: ${(service as any).kind}` };
}

async function checkService(service: ServiceCheck): Promise<ServiceHealthRecord> {
  const retries = service.retries ?? 1;
  let lastError: string | undefined;
  let bestLatency: number | undefined;

  for (let attempt = 1; attempt <= retries + 1; attempt++) {
    const result = await checkOnce(service);
    if (result.ok) {
      return {
        id: service.id,
        name: service.name,
        state: result.latencyMs > (service.timeoutMs ?? 1500) * 0.8 ? "DEGRADED" : "ONLINE",
        latencyMs: result.latencyMs,
        checkedAt: new Date().toISOString(),
        attempts: attempt,
        critical: Boolean(service.critical),
        tags: service.tags ?? [],
        fallbackCandidates: []
      };
    }
    lastError = result.error;
    bestLatency = bestLatency === undefined ? result.latencyMs : Math.min(bestLatency, result.latencyMs);
  }

  return {
    id: service.id,
    name: service.name,
    state: "OFFLINE",
    latencyMs: bestLatency,
    checkedAt: new Date().toISOString(),
    error: lastError,
    attempts: retries + 1,
    critical: Boolean(service.critical),
    tags: service.tags ?? [],
    fallbackCandidates: service.fallback ?? []
  };
}

function riskFor(record: ServiceHealthRecord): "LOW" | "MEDIUM" | "HIGH" {
  if (record.critical && record.state === "OFFLINE") return "HIGH";
  if (record.state === "OFFLINE") return "MEDIUM";
  return "LOW";
}

function proposalFor(record: ServiceHealthRecord, fallback?: FallbackTarget, index = 0): ProposalRecord {
  const suffix = fallback ? fallback.id : "review";
  return {
    proposal_id: `prop_${record.id}_${suffix}_${Date.now()}_${index}`,
    kind: fallback ? "fallback_activation" : record.critical ? "manual_intervention" : "service_review",
    target: record.id,
    reason: fallback
      ? `Service ${record.name} is ${record.state}; propose fallback ${fallback.label}: ${fallback.reason}`
      : `Service ${record.name} is ${record.state}; no automatic fallback configured.`,
    risk: riskFor(record),
    authority: ["LOCAL_FIRST", "DIAGNOSTIC_ONLY", "PROPOSAL_ONLY", "REQUIRES_AUDIT"],
    status: "DRAFT",
    createdAt: new Date().toISOString(),
    fallback
  };
}

function summarize(services: ServiceHealthRecord[], proposals: ProposalRecord[]): WatchdogReport["summary"] {
  return {
    total: services.length,
    online: services.filter((s) => s.state === "ONLINE").length,
    degraded: services.filter((s) => s.state === "DEGRADED").length,
    offline: services.filter((s) => s.state === "OFFLINE").length,
    unknown: services.filter((s) => s.state === "UNKNOWN").length,
    criticalOffline: services.filter((s) => s.critical && s.state === "OFFLINE").length,
    proposals: proposals.length
  };
}

function compactSummary(summary: WatchdogReport["summary"]): string {
  return `services=${summary.total} online=${summary.online} degraded=${summary.degraded} offline=${summary.offline} critical_offline=${summary.criticalOffline} proposals=${summary.proposals}`;
}

async function main() {
  const args = parseArgs(process.argv);
  const config = await loadConfig(args.configPath);
  const services = await Promise.all(config.map(checkService));

  const proposals = services.flatMap((record) => {
    if (record.state === "ONLINE") return [];
    if (record.fallbackCandidates.length > 0) return record.fallbackCandidates.map((fallback, index) => proposalFor(record, fallback, index));
    return [proposalFor(record)];
  });

  const summary = summarize(services, proposals);
  const report: WatchdogReport = {
    schema: "digivichi.service-watchdog.v0",
    mode: "LOCAL_FIRST",
    summary,
    services: args.full ? services : services.filter((s) => s.state !== "ONLINE"),
    proposals,
    tokenBudget: {
      compactSummary: compactSummary(summary),
      recommendedContext: summary.offline === 0 && summary.degraded === 0 ? "summary_only" : summary.offline <= 2 ? "summary_plus_failed_services" : "full_report"
    }
  };

  const json = JSON.stringify(report, null, args.full ? 2 : 0);
  if (args.outPath) await fs.writeFile(args.outPath, json + "\n", "utf8");
  console.log(json);

  if (summary.criticalOffline > 0) process.exitCode = 2;
  else if (summary.offline > 0 || summary.degraded > 0) process.exitCode = 1;
}

main().catch((err) => {
  console.error(JSON.stringify({ schema: "digivichi.service-watchdog.error.v0", error: err instanceof Error ? err.message : String(err) }));
  process.exit(2);
});
