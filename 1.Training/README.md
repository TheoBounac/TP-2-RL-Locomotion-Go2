# 🏋️ Partie 1: Entraînement 

Dans le conteneur, allez dans l’espace de travail MJLab :

```bash
cd /opt/mjlab
```

Vous devriez voir :

<p align="center">
  <img src="../doc/docker1.png" width="800">
</p>

---

Lancez l’environnement Go2 avec une politique aléatoire :

```bash
uv run play Mjlab-Velocity-Flat-Unitree-Go2 --agent random
```

Vous devriez voir :

<p align="center">
  <img src="../doc/docker2.png" width="800">
  <img src="../doc/docker3.png" width="800">
</p>

---

Vous pouvez ensuite essayer de lancer le script d’entraînement, qui est incomplet (sections à décommenter pendant le tutoriel).

Lancez l’entraînement :

```bash
uv run train Mjlab-Velocity-Flat-Unitree-Go2 --env.scene.num-envs 1024
```

Entrez le choix 3 :

<p align="center">
  <img src="../doc/docker4.png" width="800">
</p>

Vous devriez voir les logs :

<p align="center">
  <img src="../doc/docker5.png" width="800">
</p>
