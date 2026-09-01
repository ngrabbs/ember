#!/bin/bash
# Search the JLCPCB basic/preferred parts list
# Usage:
#   ./jlcpcb_parts_search.sh "10k 0402"        # free-text search
#   ./jlcpcb_parts_search.sh -b "capacitor"     # basic parts only
#   ./jlcpcb_parts_search.sh -c "MOSFET"        # search by category
#
# To update the parts list, run:
#   curl -sL "https://cdfer.github.io/jlcpcb-parts-database/jlcpcb-components-basic-preferred.csv" \
#     | python3 update_jlcpcb_parts.py

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CSV="$SCRIPT_DIR/jlcpcb_basic_preferred_parts.csv"

if [ ! -f "$CSV" ]; then
    echo "Error: Parts CSV not found at $CSV"
    echo "Download it first — see script comments."
    exit 1
fi

BASIC_ONLY=0
CAT_SEARCH=0

while getopts "bc" opt; do
    case $opt in
        b) BASIC_ONLY=1 ;;
        c) CAT_SEARCH=1 ;;
    esac
done
shift $((OPTIND - 1))

QUERY="$*"
if [ -z "$QUERY" ]; then
    echo "Usage: $0 [-b] [-c] <search terms>"
    echo "  -b  Basic parts only (no extra fee)"
    echo "  -c  Search category/subcategory columns only"
    echo ""
    echo "Parts list: $(tail -n +2 "$CSV" | wc -l) components"
    echo "  Basic:     $(grep -c ',Basic,' "$CSV")"
    echo "  Preferred: $(grep -c ',Preferred,' "$CSV")"
    exit 0
fi

# Print header
head -1 "$CSV"

# Build grep pipeline
{
    tail -n +2 "$CSV"
} | {
    if [ "$BASIC_ONLY" -eq 1 ]; then
        grep ',Basic,'
    else
        cat
    fi
} | {
    if [ "$CAT_SEARCH" -eq 1 ]; then
        # Only match in category/subcategory fields (columns 5-6)
        awk -F',' -v q="$QUERY" 'tolower($5) ~ tolower(q) || tolower($6) ~ tolower(q)'
    else
        grep -i "$QUERY"
    fi
} | awk -F',' '{printf "%-12s %-10s %-24s %-10s %-8s %s\n", $1, $2, $3, $7, $10, $8}'
