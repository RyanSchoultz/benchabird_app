# QR Results Scanning Stage 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make ticket QR codes carry `AutoNum` and let USB scanner input populate Results exhibit numbers reliably.

**Architecture:** Add a parser service that converts QR/barcode text into an exhibit number. Update ticket QR payload generation to include `AutoNum`. Wire Results exhibit field Return handling through the parser before moving focus to Result.

**Tech Stack:** Python, Peewee, qrcode, CustomTkinter, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_scan_parser_service.py` | Create | Validate scan payload parsing and legacy QR resolution |
| `tests/test_ticket_pdf_service.py` | Modify | Validate QR payload helper includes AutoNum |
| `services/scan_parser_service.py` | Create | Parse scans and resolve legacy payloads through `calculated_entry` |
| `services/ticket_pdf_service.py` | Modify | Generate QR payloads with AutoNum |
| `views/results_view.py` | Modify | Parse scanned Exhibit # field input on Return |
| `README.md` | Modify | Document USB scanner support and QR payload format |

## Task 1: Failing Parser And Payload Tests

**Files:**
- Create: `tests/test_scan_parser_service.py`
- Modify: `tests/test_ticket_pdf_service.py`

- [ ] **Step 1: Add parser tests**

Cover new QR payload, plain numeric input, old QR payload resolution, and old QR missing-match error.

- [ ] **Step 2: Add ticket payload test**

Import `_ticket_qr_payload` from `services.ticket_pdf_service` and assert it contains `AutoNum`, `ExhNo`, and `Class`.

- [ ] **Step 3: Verify RED**

Run: `python -m pytest tests/test_scan_parser_service.py tests/test_ticket_pdf_service.py -v`

Expected: import failure for `services.scan_parser_service` and missing `_ticket_qr_payload`.

## Task 2: Parser And QR Payload

**Files:**
- Create: `services/scan_parser_service.py`
- Modify: `services/ticket_pdf_service.py`

- [ ] **Step 1: Implement scan parser**

Expose:

```python
class ScanParseError(ValueError): ...
def parse_scan_to_auto_num(text: str) -> int
```

Rules:

- Empty text raises `ScanParseError`.
- Numeric text returns the integer.
- Key/value payloads accept `AutoNum`, `ExhNo`, and `Class`.
- `AutoNum` wins when present and numeric.
- Legacy `ExhNo` + `Class` resolves through `CalculatedEntry`.
- Missing/ambiguous legacy matches raise `ScanParseError`.

- [ ] **Step 2: Update ticket QR payload**

Add `_ticket_qr_payload(ticket)` and use it from `_make_qr_reader`.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest tests/test_scan_parser_service.py tests/test_ticket_pdf_service.py -v`

Expected: pass.

- [ ] **Step 4: Commit**

Commit message: `feat: add QR scan parser and AutoNum payload`

## Task 3: Results UI USB Scanner Wiring

**Files:**
- Modify: `views/results_view.py`

- [ ] **Step 1: Add `_accept_scan_or_number` handler**

On Return in Exhibit # field, parse the field with `parse_scan_to_auto_num`. If successful, replace field text with the resolved number and focus Result. If not, show the parser error.

- [ ] **Step 2: Keep Save behavior unchanged**

Result combo Return and Save button should still call `_save_result`.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest tests/test_scan_parser_service.py tests/test_ticket_pdf_service.py -v`

Expected: pass.

- [ ] **Step 4: Commit**

Commit message: `feat: wire USB scanner input into results entry`

## Task 4: Docs And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document that ticket QR codes include `AutoNum`, USB scanners can scan into the Results Exhibit # field, and webcam/mobile companion are planned follow-on stages.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest tests/ -v --tb=short`

Expected: all tests pass.

- [ ] **Step 3: Commit docs**

Commit message: `docs: document QR results scanning stage 1`

- [ ] **Step 4: Check status**

Run: `git status --short --branch`

Expected: clean working tree.
