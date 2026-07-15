#!/usr/bin/env bash
set -u

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <task-plan.md>" >&2
  exit 2
fi

plan_file=$1

if [ ! -f "$plan_file" ] || [ ! -r "$plan_file" ]; then
  echo "missing or unreadable file: $plan_file" >&2
  exit 2
fi

LC_ALL=C awk '
function trim(value) {
  sub(/^[[:space:]]+/, "", value)
  sub(/[[:space:]]+$/, "", value)
  return value
}

function strip_marker(value) {
  value = trim(value)
  sub(/^([-*+][[:space:]]+|[0-9]+\.[[:space:]]+|>[[:space:]]*)/, "", value)
  return trim(value)
}

function fail(message) {
  print "task plan error: " message
  errors = 1
}

function section_index(name, i) {
  for (i = 1; i <= section_total; i++) {
    if (sections[i] == name) {
      return i
    }
  }
  return 0
}

function field_index(line, i) {
  for (i = 1; i <= field_total; i++) {
    if (substr(line, 1, length(fields[i])) == fields[i]) {
      return i
    }
  }
  return 0
}

function is_placeholder(value, lowered) {
  value = trim(value)
  lowered = tolower(value)
  return value == "" || value ~ /^[-_]+$/ || lowered == "tbd" ||
    lowered == "todo" || lowered == "n/a" || lowered == "na" ||
    lowered == "none" || lowered == "not applicable"
}

function split_row(line, cells, raw, count, i) {
  sub(/^[[:space:]]*\|/, "", line)
  sub(/\|[[:space:]]*$/, "", line)
  count = split(line, raw, "|")
  for (i = 1; i <= count; i++) {
    cells[i] = trim(raw[i])
  }
  return count
}

function is_separator(cells, count, i) {
  if (count != 5) {
    return 0
  }
  for (i = 1; i <= count; i++) {
    if (cells[i] !~ /^:?-{3,}:?$/) {
      return 0
    }
  }
  return 1
}

BEGIN {
  section_total = 11
  sections[1] = "Plan Status"
  sections[2] = "Goal / Scope"
  sections[3] = "Context Sources Checked"
  sections[4] = "Alignment Status"
  sections[5] = "Human Alignment Log"
  sections[6] = "Task / Worktree / Branch Plan"
  sections[7] = "Contract / Behavior"
  sections[8] = "Validation Plan"
  sections[9] = "Evidence Plan"
  sections[10] = "Risks / Open Questions"
  sections[11] = "Implementation Recommendation"

  field_total = 13
  fields[1] = "Test Boundary:"
  fields[2] = "Why this boundary:"
  fields[3] = "Why not narrower:"
  fields[4] = "Why not broader:"
  fields[5] = "Dependencies:"
  fields[6] = "Command:"
  fields[7] = "Expected RED:"
  fields[8] = "Expected GREEN:"
  fields[9] = "Missing evidence policy:"
  fields[10] = "Minimum attempts before accepting missing evidence:"
  fields[11] = "Covered layers:"
  fields[12] = "Entry / Command / Artifact per layer:"
  fields[13] = "Omitted layers with reasons / risks:"

  layer_total = 7
  layers[1] = "Unit"
  layers[2] = "Component / Module"
  layers[3] = "Contract"
  layers[4] = "Mock E2E"
  layers[5] = "Real API / CLI"
  layers[6] = "Real Backend E2E"
  layers[7] = "Evidence / Demo"

  expected_section = 1
  current_section = 0
}

{
  line = $0
  sub(/\r$/, "", line)
  stripped = trim(line)

  if (stripped ~ /^##[[:space:]]+/ && stripped !~ /^###[[:space:]]+/) {
    heading = stripped
    sub(/^##[[:space:]]+/, "", heading)
    heading = trim(heading)
    h2_count++

    if (h2_count == 1 && heading != "Plan Status") {
      fail("Plan Status must be the first level-two heading")
    }

    section_number = section_index(heading)
    if (section_number == 0) {
      fail("unexpected level-two section: " heading)
      current_section = 0
    } else {
      section_seen[section_number]++
      if (section_seen[section_number] > 1) {
        fail("duplicate section: " heading)
      }
      if (section_number != expected_section) {
        fail("section out of order: " heading)
      } else {
        expected_section++
      }
      current_section = section_number
      if (section_number == 1 && NR > 8) {
        fail("Plan Status must appear within the first eight lines")
      }
    }
    next
  }

  marked = strip_marker(line)

  if (current_section == 1) {
    if (substr(marked, 1, length("Status:")) == "Status:") {
      plan_status_count++
      plan_status = trim(substr(marked, length("Status:") + 1))
    }
    if (substr(marked, 1, length("Execution:")) == "Execution:") {
      execution_count++
      execution_text = trim(substr(marked, length("Execution:") + 1))
      if (execution_text ~ /^Allowed([[:space:].:]|$)/) {
        execution = "Allowed"
      } else if (execution_text ~ /^Blocked([[:space:].:]|$)/) {
        execution = "Blocked"
      } else {
        execution = execution_text
      }
    }
  }

  if (current_section == 4 && substr(marked, 1, length("Status:")) == "Status:") {
    alignment_status_count++
    alignment_status = trim(substr(marked, length("Status:") + 1))
  }

  if (current_section != 8) {
    next
  }

  field_number = field_index(marked)
  if (field_number > 0) {
    field_seen[field_number]++
    field_value[field_number] = trim(substr(marked, length(fields[field_number]) + 1))
  }

  if (stripped !~ /^\|/) {
    next
  }

  for (key in cells) {
    delete cells[key]
  }
  for (key in raw) {
    delete raw[key]
  }
  cell_count = split_row(line, cells, raw)

  if (cells[1] == "Layer") {
    table_header_count++
    if (table_header_count > 1) {
      fail("duplicate layered validation table header")
    }
    if (cell_count != 5 || cells[2] != "Required" ||
        cells[3] != "Entry / Command / Artifact" || cells[4] != "Proves" ||
        cells[5] != "Does not prove / Risk") {
      fail("invalid layered validation table header")
    }
    table_started = 1
    next
  }

  if (!table_started) {
    fail("table row appears before the layered validation header")
    next
  }

  if (is_separator(cells, cell_count)) {
    next
  }

  table_row_count++
  if (table_row_count > layer_total) {
    fail("layered validation table has more than seven rows")
    next
  }

  if (cell_count != 5) {
    fail("layer row must contain exactly five cells: " layers[table_row_count])
    next
  }
  if (cells[1] != layers[table_row_count]) {
    fail("expected layer row " layers[table_row_count] ", found " cells[1])
  }
  if (cells[2] != "Yes" && cells[2] != "No") {
    fail("Required must be Yes or No for layer: " cells[1])
  }
  for (i = 1; i <= 5; i++) {
    if (is_placeholder(cells[i])) {
      fail("layer row contains empty or placeholder content: " cells[1])
      break
    }
  }
}

END {
  for (i = 1; i <= section_total; i++) {
    if (section_seen[i] == 0) {
      fail("missing section: " sections[i])
    }
  }

  if (plan_status_count != 1) {
    fail("Plan Status must contain exactly one Status field")
  }
  if (execution_count != 1) {
    fail("Plan Status must contain exactly one Execution field")
  }
  if (!((plan_status == "Aligned" && execution == "Allowed") ||
        (plan_status == "Draft - waiting for user alignment" && execution == "Blocked"))) {
    fail("invalid Plan Status and Execution pair")
  }
  if (alignment_status_count != 1 || alignment_status != plan_status) {
    fail("Alignment Status must contain the same Status value as Plan Status")
  }

  for (i = 1; i <= field_total; i++) {
    if (field_seen[i] != 1) {
      fail("Validation Plan must contain exactly one field: " fields[i])
    } else if (is_placeholder(field_value[i])) {
      fail("Validation Plan field is empty or a placeholder: " fields[i])
    }
  }

  attempts = field_value[10]
  if (attempts !~ /^[0-9]+$/ || attempts + 0 < 2) {
    fail("Minimum attempts before accepting missing evidence must be an integer of at least 2")
  }

  if (table_header_count != 1) {
    fail("Validation Plan must contain exactly one layered validation table")
  }
  if (table_row_count != layer_total) {
    fail("layered validation table must contain exactly seven rows")
  }

  exit errors ? 1 : 0
}
' < "$plan_file" >&2
checker_status=$?

if [ "$checker_status" -ne 0 ]; then
  exit 1
fi

echo "task plan structure check passed: $plan_file"
