# Premium Desktop UI

The premium desktop shell is an additive UI layer. Existing `apps.image_viewer`
and `apps.cell_counter` entry points and processing modules remain intact.

Run the unified desktop experience from the repository root:

```powershell
python -m apps.premium.main
```

## Structure

```text
apps/premium/
  main.py                         # unified shell and page routing
  components.py                   # metric cards, alerts and filmstrip
  workers.py                      # image-transform worker interfaces
  progressive_segmentation.py     # emits watershed stage outputs from a worker
  pages/
    image_transform_page.py       # creative image editor workflow
    cell_counter_page.py          # scientific segmentation workflow
shared/ui/
  app_shell.py                    # reusable sidebar and status strip
  image_viewport.py               # QGraphicsView-based NumPy image viewer
  segmented_control.py            # native QSS-friendly tool switcher
styles/
  colors.py                       # shared visual tokens
  theme.py                        # centralized QSS
```

## Implementation notes

- Image canvas zoom/pan affects the viewport only; it never changes processing resolution.
- Transform previews use a 100 ms debounce and keep only the most recent request.
- Watershed work executes off the main UI thread and emits each stage after that stage is computed.
- The UI uses `QSplitter` at the app page level so users can tune panel proportions.
