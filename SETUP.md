# Setup: your animated GitHub profile

## 1. Create the profile repository
Create a **public** repo named exactly **`Adel-Lis`**. GitHub shows its README on your profile page.

## 2. Upload everything in this folder
Keep the structure:

```
Adel-Lis/
├── README.quant.md   README.lab.md   README.matrix.md   README.poster.md
├── assets/{quant,lab,matrix,poster}/   (banners, cards, headers, globe, buttons)
├── scripts/activity3d.py               (3D skyline generator)
├── .github/workflows/activity.yml      (daily snake + skyline)
└── previews/                           (screenshots, safe to delete)
```

The `.github` folder is hidden on macOS and Linux. Make sure it gets uploaded too (drag-and-drop in the GitHub web UI works, or use `git push`).

## 3. Pick your version
Rename the one you want to **`README.md`**. The other three can stay, since each only uses its own `assets/<version>/` folder. You can switch any time by renaming a different file.

| File | Look |
|---|---|
| `README.quant.md` | Bloomberg-style trading terminal |
| `README.lab.md` | Research paper, with an ES population on a loss landscape |
| `README.matrix.md` | Code rain, glitch type, shell-command sections |
| `README.poster.md` | Retro-futurist poster, with a slit sun and a perspective grid |

## 4. Turn on the activity art (snake + 3D skyline)
1. Go to repo **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**.
2. Go to **Actions → activity-art → Run workflow**.
3. After about a minute an `output` branch appears. The README's Activity section reads from it. It refreshes every day at 03:00 UTC.

Until the first run finishes, those two images show as broken. That's expected.

To count private-repo work in the skyline, go to **Profile → Contribution settings** and tick "Include private contributions".

## 5. Later: CV + talk-with-me
At the bottom of your chosen README there's a commented-out closing section. Replace `YOUR_CV_LINK` and `YOUR_TALK_WITH_ME_LINK`, then delete the two lines containing only `<!--` and `-->`.

## Notes
- The **multi_agent_market_simulator** card links to `github.com/Adel-Lis/multi_agent_market_simulator`. If that repo is private or named differently, update the link in the README.
- All fonts are embedded inside the SVGs, so they render exactly as designed. GitHub blocks external fonts.
- Animations respect "reduce motion" system settings.
- The rotating titles use readme-typing-svg (an external service), in each version's own font.
