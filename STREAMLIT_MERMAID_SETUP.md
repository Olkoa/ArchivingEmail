# Installation de streamlit-mermaid (Optionnel)

## Pourquoi installer streamlit-mermaid ?

L'installation de `streamlit-mermaid` améliore l'affichage des diagrammes Mermaid dans l'application en offrant :
- **Meilleure performance** : Rendu natif plus rapide
- **Interactivité améliorée** : Support des clics et zoom
- **Intégration seamless** : Pas besoin de composants HTML externes

## Installation

```bash
pip install streamlit-mermaid
```

## Vérification de l'installation

Après installation, redémarrez l'application Streamlit. La page "Structure de la boîte mail" utilisera automatiquement `streamlit-mermaid` si disponible.

## Alternative sans installation

Si vous ne souhaitez pas installer `streamlit-mermaid`, l'application fonctionne parfaitement avec notre solution HTML intégrée qui utilise Mermaid.js via CDN.

## Test de fonctionnement

Pour tester si `streamlit-mermaid` est correctement installé :

1. Allez à la page **Visualization** > **Structure de la boîte mail**
2. Générez un diagramme
3. Si `streamlit-mermaid` est installé, vous verrez un rendu plus fluide
4. Sinon, le diagramme s'affichera via notre solution HTML de secours

## Dépannage

### ImportError: No module named 'streamlit_mermaid'
**Solution :** Installez le package avec `pip install streamlit-mermaid`

### Le diagramme ne s'affiche pas
**Solutions :**
1. Vérifiez votre connexion internet (pour le CDN Mermaid.js)
2. Essayez de rafraîchir la page
3. Utilisez le lien vers l'éditeur Mermaid en ligne fourni en secours

### Erreur de rendu
**Solutions :**
1. Vérifiez que le code Mermaid est valide
2. Régénérez le diagramme avec le bouton "Générer le graphique"
3. Téléchargez le fichier .mermaid et utilisez un éditeur externe

### Performance lente
**Solutions :**
1. Installez `streamlit-mermaid` pour de meilleures performances
2. Réduisez la complexité du diagramme si nécessaire
3. Utilisez l'éditeur en ligne pour les diagrammes très complexes

## Comparaison des méthodes d'affichage

| Méthode | Avantages | Inconvénients |
|---------|-----------|---------------|
| **streamlit-mermaid** | Performance optimale, interactivité native | Dépendance externe |
| **HTML + Mermaid.js** | Aucune dépendance, fonctionne partout | Légèrement plus lent |
| **Editeur en ligne** | Interface dédiée, export facile | Nécessite copier-coller |

## Configuration avancée

Si vous utilisez `streamlit-mermaid`, vous pouvez personnaliser les options :

```python
# Dans le code de l'application
from streamlit_mermaid import st_mermaid

# Configuration personnalisée
config = {
    'theme': 'default',
    'themeVariables': {
        'primaryColor': '#4285F4',
        'primaryTextColor': '#fff',
        'primaryBorderColor': '#1976D2'
    }
}

st_mermaid(mermaid_code, height=600, config=config)
```

## Support et ressources

- **Documentation Mermaid :** https://mermaid.js.org/
- **Streamlit-mermaid GitHub :** https://github.com/andfanilo/streamlit-mermaid
- **Éditeur en ligne :** https://mermaid.live/
- **Exemples de diagrammes :** https://mermaid.js.org/syntax/flowchart.html
