import type { ApiCall } from '../api';

/** Exports the currently visible API call logs. UTF-8 BOM supports Korean Excel. */
const headers = ['api_call_id','run_id','provider','api_type','http_status','success','latency_ms','error_source','error_code','called_at'];
function csvCell(value: unknown): string {
  const raw = value == null ? '' : String(value);
  // Avoid spreadsheet formula injection when opening downloaded CSV in Excel.
  const safe = /^[\s\u0000-\u001f]*[=+@-]/.test(raw) ? "'" + raw : raw;
  return '"' + safe.replace(/"/g, '""') + '"';
}
export function exportApiCallsCsv(calls: ApiCall[]): void {
  const rows = calls.map(c => [c.api_call_id,c.run_id,c.provider,c.api_type,c.http_status,c.success,c.latency_ms,c.error_source,c.error_code,c.called_at]);
  const content = [headers.map(csvCell).join(','), ...rows.map(row => row.map(csvCell).join(','))].join('\r\n');
  const blob = new Blob(['\uFEFF', content], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `api-call-logs-${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
