#!/usr/bin/env bash
# Download administrative boundary files for OpenDengue unit matching; append to manifests/boundaries.tsv.
# Usage (from project root, env sourced): bash scripts/data/download_boundaries.sh
set -euo pipefail
P=$(cd "$(dirname "$0")/../.." && pwd); cd "$P"
R=data/raw/boundaries; M=manifests/boundaries.tsv
mkdir -p "$R" manifests
[ -f "$M" ] || printf 'file\tsource_url\tbytes\tsha256\tlicence\tupstream_checksum\tdownloaded_at_utc\n' > "$M"
fetch() { # dir url outname licence upstream
  local d="$R/$1" url="$2" out="$3" lic="$4" up="${5:-}"
  mkdir -p "$d"
  if [ ! -s "$d/$out" ]; then curl -fsSL --retry 3 --max-time 1800 -o "$d/$out" "$url"; fi
  local b s; b=$(stat -c %s "$d/$out"); s=$(sha256sum "$d/$out" | cut -d' ' -f1)
  grep -q "^$d/$out	" "$M" || printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$d/$out" "$url" "$b" "$s" "$lic" "$up" "$(date -u +%FT%TZ)" >> "$M"
}
# Brazil: IBGE malha municipal 2022
IBGE=https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/Brasil/BR/BR_Municipios_2022.zip
fetch ibge "$IBGE" BR_Municipios_2022.zip "IBGE open data (free use with attribution)" "none published"
# geoBoundaries gbOpen (pinned commit via API gjDownloadURL)
for iso in COL PER TWN; do for lvl in ADM1 ADM2; do
  meta=$(curl -fsSL "https://www.geoboundaries.org/api/current/gbOpen/$iso/$lvl/")
  url=$(python -c 'import json,sys;print(json.loads(sys.argv[1])["gjDownloadURL"])' "$meta")
  lic=$(python -c 'import json,sys;print(json.loads(sys.argv[1])["boundaryLicense"])' "$meta")
  fetch geoboundaries "$url" "geoBoundaries-$iso-$lvl.geojson" "$lic" "none published"
done; done
# Taiwan: the official MOI/NLSC file (data.gov.tw dataset 7441, TGOS host) returned HTTP 403 from this server
# (2026-11-16) and GADM 4.1 TWN stops at county level (22 units), so townships come from geoBoundaries
# gbOpen TWN ADM2 (OSM-derived, 369 units), downloaded in the loop above.
