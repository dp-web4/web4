pip install maturin
cd python
maturin develop
cd simulations

# Attack simulations
python attack_simulations.py               # Core attack simulation framework
python attack_track_fb.py                  # Trust manipulation attacks
python attack_track_fc.py                  # Economic attacks

# For full 4-Life game demos, see: https://github.com/dp-web4/4-life
