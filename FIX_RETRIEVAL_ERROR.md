# Fix for `expected 3, got 2`

This version removes tuple-unpacking from retrieval ingestion and makes PDF failures non-fatal.

## Replace your local project

1. Stop Streamlit with `Ctrl+C`.
2. Extract this ZIP again into a fresh folder.
3. Copy your real `data/ParcelPilot_Assessment_Data.xlsx` into `data/`.
4. Copy the six assessment PDFs into `data/documents/`.
5. Open a terminal in the project root.
6. Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

If the old error still appears, you are running a different copy of `app.py`. In the terminal, run:

```bash
python -c "import os; print(os.path.abspath('app.py'))"
```

Then make sure that path points to the newly extracted project.
