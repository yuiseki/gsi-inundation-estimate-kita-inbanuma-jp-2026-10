# gsi-inundation-estimate-kita-inbanuma-jp-2026-10

Scripts that fetch the GSI (国土地理院) 浸水推定図 of 北印旛沼 (令和8年台風第25号) in its four versions, convert them to GeoParquet,
verify the result against GDAL, and publish it.

The data and its card are on Hugging Face: <https://huggingface.co/datasets/yuiseki/gsi-inundation-estimate-kita-inbanuma-jp-2026-10>
(published at revision `e760fbab7cdad6bc7de9adf78320cf3eca7ff288`; `docs/revision.json`). Source:
<https://www.gsi.go.jp/BOUSAI/R8_taihuu25gou.html>.

- `scripts/01_fetch`: fetch (one request at a time; the GSI server needs a TLS legacy renegotiation, set per connection in Python only).
- `scripts/02_build`, `03_verify`, `04_figure`, `05_card`: GeoParquet, the GDAL cross-check, the figure, the card.
- `src/publish.py`, `scripts/06_verify_hub`: the publication and the read-back from the Hub.

The code is MIT (`LICENSE`); the data is under the GSI's terms (PDL1.0), see the card on Hugging Face.
