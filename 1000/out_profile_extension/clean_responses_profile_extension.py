import os, re, json

# paths
INPUT_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response"
OUTPUT_FOLDER = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_clean"
ERROR_FOLDER  = r"C:/Users/Juan/Desktop/TFM/1000/out_profile_extension/response_errors"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)

FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)

def read_text(path: str) -> str:
    """Reads file content trying multiple encodings."""
    with open(path, "rb") as f:
        data = f.read()

    # common BOMs
    if data.startswith(b"\xff\xfe"):  # UTF-16 LE BOM
        return data.decode("utf-16-le")
    if data.startswith(b"\xfe\xff"):  # UTF-16 BE BOM
        return data.decode("utf-16-be")
    if data.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
        return data.decode("utf-8-sig")

    try:
        return data.decode("utf-8")
    except:
        return data.decode("latin-1", errors="replace")

def strip_fences(s: str) -> str:
    return FENCE_RE.sub("", s).strip()

def json_pretty(s: str) -> str | None:
    """Attempts to parse and prettify JSON string. Returns None if invalid."""
    try:
        return json.dumps(json.loads(s), ensure_ascii=False, indent=2)
    except Exception:
        return None

# utilities: Balanced scanning respecting strings/escapes
def find_balanced_block(s: str, open_pos: int, open_ch='{', close_ch='}'):
    """
    If s[open_pos] is '{', returns the index of the closing '}' 
    (respecting strings and escape characters).
    """
    assert s[open_pos] == open_ch
    depth = 1
    i = open_pos + 1
    in_str = False
    esc = False
    n = len(s)

    while i < n:
        ch = s[i]
        if in_str:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': in_str = False
        else:
            if ch == '"': in_str = True
            elif ch == open_ch: depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return None


def find_key_object_span(s: str, key: str, start: int, end: int):
    """
    Searches within s[start:end] for the pattern '"key": { ... }'
    Returns (key_start, key_end, brace_open, brace_close) in absolute indices, or None.
    """
    pat = re.compile(rf'"{re.escape(key)}"\s*:\s*{{')
    m = pat.search(s, start, end)

    if not m:
        return None

    brace_open = m.end() - 1
    brace_close = find_balanced_block(s, brace_open, '{', '}')

    if brace_close is None:
        return None
    if brace_close > end:
        return None

    return (m.start(), m.end(), brace_open, brace_close)


def find_dialogue_id(s: str) -> str | None:
    m = re.search(r'"dialogue_id"\s*:\s*"([^"]+)"', s)
    return m.group(1) if m else None


def find_profiles_header(s: str):
    """Returns (key_start, key_end, brace_open) for '"profiles": {' or None."""
    m = re.search(r'"profiles"\s*:\s*{', s)
    if not m: return None
    return (m.start(), m.end(), m.end()-1)


def find_member_header(s: str, who: str, start: int, end: int):
    """
    Returns (header_start, brace_open) for '"A": {' or '"B": {' 
    within [start:end], or None.
    """
    pat = re.compile(rf'"{re.escape(who)}"\s*:\s*{{')
    m = pat.search(s, start, end)
    if not m: return None
    return (m.start(), m.end()-1)


# Bracket sanitizer to fix stray ']' in arrays
def balance_brackets(raw: str) -> str:
    """
    Removes stray ']' that break arrays; respects strings/escapes.
    Useful for LLM output that hallucinates extra closing brackets.
    """
    out = []
    depth = 0
    in_str = False
    esc = False

    for ch in raw:
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
                out.append(ch)
            elif ch == '[':
                depth += 1
                out.append(ch)
            elif ch == ']':
                if depth > 0:
                    depth -= 1
                    out.append(ch)
                else:
                    # Orphan ']' -> skip it
                    continue
            else:
                out.append(ch)
    return ''.join(out)


def reconstruct_from_members(raw: str) -> str:
    """
    Reconstructs a clean JSON using:
      - dialogue_id
      - profiles.A: profile_struct + profile_narrative
      - profiles.B: profile_struct + profile_narrative
    
    It searches for each sub-object within the A and B spans, 
    even if the main closing braces are missing.
    """
    s = strip_fences(raw)

    # 1) if it is already valid JSON, prettify and return
    pretty = json_pretty(s)
    if pretty is not None:
        return pretty

    did = find_dialogue_id(s) or ""

    # 2) locate header for "profiles": {
    prof = find_profiles_header(s)
    if not prof:
        return s
    _, _, prof_open = prof
    end_limit = len(s)

    # 3) headers for A and B
    hdrA = find_member_header(s, "A", prof_open+1, end_limit)
    hdrB = find_member_header(s, "B", prof_open+1, end_limit)

    if not hdrA or not hdrB:
        return s

    (a_start, a_open) = hdrA
    (b_start, b_open) = hdrB

    if a_start < b_start:
        A_span = (a_open+1, b_start)   # raw content of A
        B_span = (b_open+1, end_limit) # raw content of B
    else:
        B_span = (b_open+1, a_start)
        A_span = (a_open+1, end_limit)

    def extract_struct_and_narrative(span):
        lo, hi = span
        ps = find_key_object_span(s, "profile_struct", lo, hi)
        pn = find_key_object_span(s, "profile_narrative", lo, hi)
        return ps, pn

    A_ps, A_pn = extract_struct_and_narrative(A_span)
    B_ps, B_pn = extract_struct_and_narrative(B_span)
    if not (A_ps and A_pn and B_ps and B_pn):
        return s

    # exact text for '"profile_struct": {...}' and '"profile_narrative": {...}'
    A_ps_text = s[A_ps[0]:A_ps[3]+1]
    A_pn_text = s[A_pn[0]:A_pn[3]+1]
    B_ps_text = s[B_ps[0]:B_ps[3]+1]
    B_pn_text = s[B_pn[0]:B_pn[3]+1]

    # 4) parse sub-objects with bracket sanitization
    def parse_sub(text):
        # text es "  "profile_struct": { ... }"
        m = re.search(r':\s*({.*})\s*$', text, re.DOTALL)
        if not m:
            m = re.search(r':\s*({.*})', text, re.DOTALL)
        if not m:
            raise ValueError("Could not extract JSON object from sub-block.")

        inner = m.group(1)
        inner_fixed = balance_brackets(inner)
        return json.loads(inner_fixed)

    A_struct = parse_sub(A_ps_text)
    A_narr   = parse_sub(A_pn_text)
    B_struct = parse_sub(B_ps_text)
    B_narr   = parse_sub(B_pn_text)

    rebuilt_obj = {
        "dialogue_id": did,
        "profiles": {
            "A": {
                "profile_struct": A_struct,
                "profile_narrative": A_narr
            },
            "B": {
                "profile_struct": B_struct,
                "profile_narrative": B_narr
            }
        }
    }
    return json.dumps(rebuilt_obj, ensure_ascii=False, indent=2)

# file processing
def process_file(inpath: str):
    raw = read_text(inpath)
    fixed = reconstruct_from_members(raw)
    base = os.path.splitext(os.path.basename(inpath))[0]
    outpath = os.path.join(OUTPUT_FOLDER, base + ".json")

    with open(outpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(fixed)

def main():
    files = [f for f in sorted(os.listdir(INPUT_FOLDER)) if f.lower().endswith(".txt")]
    ok, fail = 0, []
    for fname in files:
        inpath = os.path.join(INPUT_FOLDER, fname)
        try:
            process_file(inpath)
            ok += 1
        except Exception as e:
            fail.append((fname, str(e))) # save the bad file to error folder for inspection
            with open(os.path.join(ERROR_FOLDER, os.path.splitext(fname)[0] + ".bad.txt"),
                      "w", encoding="utf-8") as ef:
                ef.write(read_text(inpath))
    print(f"Processed: {len(files)} | OK: {ok} | Failed: {len(fail)}")
    if fail:
        print("Failed files (first 10):", [n for n,_ in fail[:10]])
        print(f"Raw errors saved in: {ERROR_FOLDER}")

if __name__ == "__main__":
    main()
