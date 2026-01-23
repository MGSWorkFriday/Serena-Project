# breathing_logic.py
import math

def calculate_breath_y(t_in_cycle, a, b, c, d):
    """
    Berekent de Y-waarde (-1 tot 1) voor de ademhalingsgrafiek.
    a = Inademtijd
    b = Hold (na in)
    c = Uitademtijd
    d = Hold (na uit)
    """
    if a + b + c + d <= 0: 
        return 0.0

    # Fase 1: Inademing (Sinus opgaand)
    if t_in_cycle < a and a > 0:
        return math.sin(-math.pi/2 + math.pi*(t_in_cycle/max(1e-6,a)))
    
    t = t_in_cycle - a
    
    # Fase 2: Hold 1 (Bovenin vast)
    if t < b and b > 0: 
        return 1.0
    
    t -= b
    
    # Fase 3: Uitademing (Sinus neergaand)
    if t < c and c > 0:
        return math.sin(math.pi/2 + math.pi*(t/max(1e-6,c)))
    
    # Fase 4: Hold 2 (Onderin vast) -> implied -1.0 return
    return -1.0