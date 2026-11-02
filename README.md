# HAR Totals

Free MIT-licensed command-line preview from Gong LLC. Summarize a saved UTF-8 HAR file as aggregate JSON without copying URL, header, cookie, content, IP, or other source text fields into the report.

Requires Python 3.12 or newer; no dependencies, browser, service, or network connection. Run in a trusted directory:

```sh
python3 har_totals.py example.har
python3 har_totals.py your-export.har > totals.json
python3 -m unittest -v
```

The supplied example is synthetic: two entries, 20 milliseconds summed entry time, 12.5 milliseconds maximum entry time, one 2xx and one 4xx response, 120 known body bytes and one unknown body size.

Output fields:

- `entry_count` and `status_counts`: status 0 is counted as `no_response`.
- `sum_entry_time_ms`: sum of per-entry `time`, **not page load time**. Requests can overlap.
- `max_entry_time_ms`: largest entry time; null for an empty log.
- `known_response_body_bytes`: sum of nonnegative `response.bodySize` values, not total network transfer size.
- `unknown_response_body_size_count`: entries whose `bodySize` is -1; these contribute nothing to the known-byte sum.

Exit 0 means a report was written; exit 2 means invalid, unsupported, oversized or unreadable input. Errors contain no source excerpt or input path. The CLI does not modify its input. Shell redirection can overwrite an existing report; use a fresh output filename.

## Limits and data handling

Maximum input: 16 MiB and 10,000 entries. Requires `log.entries`, each entry's nonnegative numeric `time`, integer `response.status` (0 or 100–599), and integer `response.bodySize` (-1 or nonnegative). Numeric magnitudes are capped at 10^12. A UTF-8 byte-order mark is accepted. Duplicate object keys, invalid UTF-8 and nonfinite numbers are rejected. This is a narrow aggregator, not a complete HAR schema validator or a browser performance profiler.

HAR files can contain sensitive data. This tool reads and parses the entire bounded input locally; do not upload the original file to a public issue. Output excludes source text fields, but aggregate counts, timings and sizes can themselves be sensitive. Review a report before sharing. This is not a sanitized HAR exporter, a secret detector, or a guarantee against malicious resource-exhaustion inputs. Python's JSON parser and process memory limits still apply. Reports cannot reconstruct request-level diagnostics or explain causes of latency.

Candidate tests run on Linux/Python 3.12; Windows and macOS are untested. No support SLA. Report setup problems or bugs without attaching private HAR data.
