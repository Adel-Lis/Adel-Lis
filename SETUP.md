# Setup: your animated GitHub profile

Public repo named exactly **`Adel-Lis`**. Upload everything in this folder, keeping the structure:

```
Adel-Lis/
├── README.md            main version (poster), shown on your profile
├── README.lab.md        the researcher
├── README.matrix.md     the engineer
├── README.quant.md      the quant
├── assets/{poster,lab,matrix,quant}/   all panels, cards, maps
├── assets/fonts/        fonts the Action embeds into the 3D city
├── scripts/activity3d.py
└── .github/workflows/activity.yml      (hidden folder, make sure it uploads)
```

The personality switchers link between the four READMEs automatically.

## Activity art (3D contribution city)
1. Settings → Actions → General → Workflow permissions → **Read and write**.
2. Actions → **activity-art** → Run workflow (or just commit any change to the workflow or script).
3. It publishes `activity-<theme>.svg` to the `output` branch and refreshes daily at 03:00 UTC.

## CV + talk-with-me
Each README ends with a commented-out closing section. Replace `YOUR_CV_LINK` and `YOUR_TALK_WITH_ME_LINK`,
then delete the two lines containing only `<!--` and `-->`.
