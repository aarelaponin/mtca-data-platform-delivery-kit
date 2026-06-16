# PowerBuilder extraction notes

Why the script works the way it does, and what to check if it under- or over-extracts.

## How PowerBuilder stores meaning in `.pbl`

A `.pbl` is a binary container, but the parts we care about are stored as **readable text**:

- **Encoding is UTF-16LE.** Every ASCII character is followed by a `0x00` byte. A naïve
  `grep`/`pdftotext`/`strings` pass either finds nothing or finds garbage. The script decodes
  with `utf-16-le` and falls back to `latin-1` only if that yields more `FROM` tokens. This single
  detail is the most common reason ad-hoc attempts fail. (In the BOP run, raw UTF-16LE decode
  surfaced ~902 `FROM` and ~773 `SELECT` tokens; the byte-level grep found 0.)
- **PowerBuilder escapes quotes** as `~"` and `~'`. The script normalises these so embedded SQL
  string literals parse cleanly.

## Where table names live

1. **Embedded SQL** — `SELECT … FROM <table>`, `JOIN <table>`, `UPDATE <table>`,
   `INSERT INTO <table>`, `DELETE FROM <table>`. Strongest signal for *operational* tables
   (those the module writes).
2. **DataWindow data sources** — `DBNAME="<table>.<column>"` and `TABLE(NAME="<table>")`.
   Strongest signal for *read* tables and the only place you get authoritative `table.column`
   pairs for free.

The script keeps the *context* (FROM/JOIN/UPDATE/INSERT/DELETE/DataWindow) per table so you can
tell a written table from a merely-read one.

## Where column names live

Two sources, very different yield depending on how the module was built:

- **Authoritative `dbname="table.col"` pairs** from DataWindow column definitions. Clean and
  unambiguous — but only present when the DataWindow spells out the table. In the BOP module only
  2 tables did this (`country`, `street`); most used the prefix convention instead.
- **Column-prefix families.** Legacy MTCA tables name every column with a short table-derived
  prefix: `taxpayer` → `tax_serial`, `tax_name`, `tax_vatno`; `country` → `cou_serial`,
  `cou_name`. The script harvests all `prefix_suffix` tokens, drops PowerBuilder UI/variable
  prefixes (`ll_`, `ls_`, `dw_`, `lbl_`, …), and groups the rest into families. This is the main
  column signal for prefix-convention modules and is how the BOP run reached 141 columns.

### Compute-copy `c*` families

DataWindow **computed columns** frequently mirror a real family with a leading `c`
(`ctax_*` mirrors `tax_*`, `ccou_*` mirrors `cou_*`). These are display duplicates, not new
columns. The script folds any `c<prefix>` family back into `<prefix>` so a column isn't counted
twice. If you see a `c*`-prefixed column survive, it's because its base prefix wasn't itself a
family — check whether it's real.

## Prefix → table auto-mapping (and why some are left for you)

The script maps a prefix to a table only when it is confident: the prefix is a literal prefix of
exactly one candidate table (`cou` → `country`, `acc` → `accountperiod`). It deliberately does
**not** guess when:

- the prefix is an **abbreviation or initialism** (`bym` → `bopyearmember`, `cin` → `coincentive`,
  `wfl` → `whitefile`, `sbc` → `subcategory`) — no literal match exists;
- the prefix is **ambiguous** (`tax` matches both `taxpayer` and `taxpayerlock`);
- the table the prefix belongs to **isn't in the candidate list at all** (`em` → `employer`,
  `rol` → `role`), usually because the inventory missed it.

These land in `unmapped_prefixes_for_human`. Mapping them is a judgement call the model running the
skill makes from the column names and domain — see the table in `SKILL.md` §3.

## Noise the script filters (and the residue you finish)

- **RDBMS/driver/status tokens** that appear inside SQL or message strings (`informix`, `failed`,
  `dual`, `sysmaster`) are denylisted, as are tokens shorter than 3 chars.
- **Framework tables** (`administrator`, `application`, `list`, `parameter`, `std_message`,
  `sect`) can still pass when they exist in the inventory, because they are real tables — they're
  just not *this module's* business data. The script can't know intent, so you prune these in
  Workflow step 2.
- **Short noise prefixes** (`ird`, `fsse`, single-column families) are suppressed by requiring a
  family to have ≥2 distinct columns before it's surfaced as unmapped.

## If extraction looks wrong on a new module

- **Few/no tables?** Check the decode — open the `.pbl`, confirm UTF-16LE. If it's a different PB
  version or an exported `.sr*` source, the text may be single-byte; the fallback handles that but
  verify the `FROM` count looks sane.
- **Too much noise?** Provide an inventory if you didn't, or extend `TABLE_NOISE` / `PB_COL_PREFIX`
  in the script for that codebase's conventions.
- **Columns missing for a known table?** Its prefix is probably in `unmapped_prefixes_for_human`
  or was folded as a `c*` duplicate — check the families in the JSON.
