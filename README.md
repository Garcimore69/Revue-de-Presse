# Revue de presse

App statique qui affiche chaque matin des titres/aperçus d'articles filtrés par
thématique, à partir de flux RSS (aucune clé API, aucun compte requis).

## Fonctionnement

- `scripts/fetch_news.py` lit `config/sources.json` (médias + flux RSS) et
  `config/themes.json` (thématiques + mots-clés FR/EN/ES), récupère les
  articles, les filtre par mots-clés, et écrit `docs/articles.json`.
- `.github/workflows/update-news.yml` exécute ce script chaque jour via
  GitHub Actions (cron) et commit le résultat.
- `docs/index.html` est une page statique qui lit `docs/articles.json` et
  affiche la revue de presse. Vos sujets/langues favoris sont mémorisés
  dans le navigateur (localStorage), aucun compte nécessaire.

## Déploiement (une seule fois)

1. Créez un nouveau repo GitHub (public ou privé) et poussez ce dossier.
2. Dans **Settings → Pages**, choisissez la branche `main` et le dossier `/docs`.
3. Dans **Settings → Actions → General → Workflow permissions**, cochez
   **"Read and write permissions"** (nécessaire pour que l'action commit
   `articles.json`).
4. Lancez le workflow une première fois manuellement : onglet **Actions** →
   "Mise à jour revue de presse" → **Run workflow**. Cela génère un premier
   `articles.json`.
5. Votre app sera accessible à `https://<votre-utilisateur>.github.io/<repo>/`.

## Horaire (important)

Le cron GitHub (`0 5 * * *`) est calé en UTC et correspond à **6h à Paris en
heure d'hiver**. En heure d'été (fin mars à fin octobre), cela correspond en
réalité à 7h. GitHub Actions ne gère pas nativement les fuseaux avec heure
d'été — deux options :
- laisser tel quel (léger décalage l'été),
- ou modifier manuellement le cron dans `.github/workflows/update-news.yml`
  à `'0 4 * * *'` autour des changements d'heure (fin mars / fin octobre).

Le déclenchement `schedule` de GitHub peut aussi avoir quelques minutes de
retard aux heures de forte charge : c'est une limite connue du service, pas
un bug de la config.

## Sources à vérifier

`config/sources.json` contient une entrée par média que vous avez demandé.
Certaines URL de flux RSS sont **confirmées** (`"verified": true`), d'autres
sont des **estimations** (`"verified": false`) à tester, et quelques-unes
sont **désactivées** (`"disabled": true`) faute de flux RSS disponible
(ex : Le Canard Enchaîné, The Times, Rue89 — fusionné avec L'Obs depuis 2018).
Pour corriger une URL : éditez le champ `url`, relancez le workflow
manuellement pour vérifier que ça fonctionne (regardez les logs de l'étape
"Récupérer et filtrer les articles" — les flux en échec y sont listés en
`[WARN]` mais n'empêchent jamais le run de continuer).

## Ajuster les thématiques

Éditez `config/themes.json` : chaque thème a une liste de mots-clés par
langue (`keywords_fr`, `keywords_en`, `keywords_es`). Le filtrage se fait
par simple recherche de sous-chaîne dans le titre + résumé de chaque
article. Vous pouvez ajouter/retirer des mots-clés ou des thèmes entiers
librement — la page s'adapte automatiquement aux clés présentes dans ce
fichier.

## Tester en local

```bash
pip install feedparser requests
python scripts/fetch_news.py
cd docs && python -m http.server 8000
# puis ouvrir http://localhost:8000
```

## Limites connues

- Le filtrage par mots-clés est simple (pas de NLP) : il peut manquer des
  articles pertinents ou en inclure des non pertinents. Affinez les
  mots-clés dans `themes.json` selon ce que vous observez.
- Certains sites (Times, Telegraph, Rue89) n'ont pas de flux RSS public
  exploitable et sont désactivés par défaut.
- Les flux marqués `"verified": false` n'ont pas été testés en conditions
  réelles ; corrigez-les au besoin après le premier run.
