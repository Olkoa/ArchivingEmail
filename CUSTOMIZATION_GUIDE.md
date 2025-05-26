# 🎨 Guide des nouvelles options de personnalisation

## 📊 Orientation du graphique

### Quand utiliser l'orientation verticale (📊)
- **Structure profonde** : Plusieurs niveaux de sous-dossiers
- **Hiérarchie traditionnelle** : Structure organisationnelle classique
- **Écrans normaux** : Affichage standard sur ordinateur
- **Impression** : Format portrait pour documents

**Exemple :** 
```
📧 Racine
├── 📥 Boîte de réception
│   ├── 📁 Projets
│   └── 📁 Admin
├── 📤 Envoyés
└── 🗑️ Supprimés
```

### Quand utiliser l'orientation horizontale (📈)
- **Structure large** : Beaucoup de dossiers au même niveau  
- **Présentations** : Diaporamas et écrans larges
- **Flux de processus** : Visualisation de workflow
- **Écrans ultra-larges** : Moniteurs 21:9 ou multi-écrans

**Exemple :**
```
📧 Racine → 📥 Boîte de réception → 📁 Projets → 📁 Projet A
                                   → 📁 Admin   → 📁 Factures
           → 📤 Envoyés
           → 🗑️ Supprimés
```

## 🔤 Taille du texte

### Petit (10px) - 🔤
**Utilisation :**
- Structures très complexes avec 20+ dossiers
- Diagrammes détaillés pour analyse
- Économie d'espace sur petit écran

**Avantages :** Compact, beaucoup d'informations
**Inconvénients :** Moins lisible

### Normal (12px) - 🔤 (Recommandé)
**Utilisation :**
- Usage général et quotidien
- Structures moyennes (5-15 dossiers)
- Équilibre lisibilité/compacité

**Avantages :** Bon compromis, lisible
**Inconvénients :** Aucun

### Grand (14px) - 🔤
**Utilisation :**
- Meilleure lisibilité
- Présentations en petite salle
- Accessibilité améliorée

**Avantages :** Plus lisible, professionnel
**Inconvénients :** Prend plus de place

### Très grand (16px) - 🔤
**Utilisation :**
- Présentations en grand amphithéâtre
- Accessibilité maximale
- Démonstrations publiques
- Personnes malvoyantes

**Avantages :** Très lisible, impact visuel
**Inconvénients :** Encombrant

## 🎯 Combinaisons recommandées

### Pour l'analyse quotidienne
- **Orientation :** Verticale 📊
- **Taille :** Normale (12px) 🔤
- **Usage :** Travail quotidien, analyse des dossiers

### Pour les présentations
- **Orientation :** Horizontale 📈
- **Taille :** Grande (14px) ou Très grande (16px) 🔤
- **Usage :** Réunions, formations, démonstrations

### Pour les structures complexes
- **Orientation :** Verticale 📊
- **Taille :** Petite (10px) 🔤  
- **Usage :** Analyse détaillée, documentation technique

### Pour l'accessibilité
- **Orientation :** Selon préférence
- **Taille :** Très grande (16px) 🔤
- **Usage :** Personnes malvoyantes, affichage public

## 🛠️ Comment changer les options

1. **Accédez à la page :** Visualization > Structure de la boîte mail
2. **Sélectionnez l'orientation :** Radio buttons 📊/📈
3. **Choisissez la taille :** Menu déroulant 🔤
4. **Générez :** Cliquez sur "🔄 Générer le graphique"
5. **Téléchargez :** Le nom du fichier inclut vos options

## 📁 Noms de fichiers

Les fichiers téléchargés incluent maintenant vos options :
- `Projet_Demo_mail_structure_vertical_normal.mermaid`
- `Projet_Demo_mail_structure_horizontal_large.mermaid`

## 🔄 Persistance des options

- ✅ **Options sauvées** dans la session Streamlit
- ✅ **Détection automatique** des options dans les fichiers existants  
- ✅ **Affichage des paramètres** actuels dans l'interface
- ✅ **Historique** des options utilisées

## 🚀 Conseils d'utilisation

### Optimisation pour différents usages

**📱 Mobile/Tablette :**
- Orientation : Verticale
- Taille : Normale ou Grande

**🖥️ Desktop :**
- Orientation : Au choix
- Taille : Normale

**📺 Présentation :**
- Orientation : Horizontale (recommandé)
- Taille : Grande ou Très Grande

**🖨️ Impression :**
- Orientation : Verticale
- Taille : Normale

### Workflow recommandé

1. **Commencez** avec Vertical + Normal
2. **Testez** Horizontal si structure large
3. **Ajustez** la taille selon le contexte
4. **Sauvegardez** différentes versions si besoin

Profitez de ces nouvelles options pour créer des diagrammes parfaitement adaptés à vos besoins ! 🎉
