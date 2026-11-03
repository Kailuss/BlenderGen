"""Magnitudes explícitas del sustituto de impacto, sin dependencia de Blender."""
import math


def positive(value, label):
    """IA: Rechaza datos no finitos o no positivos antes de derivar magnitudes físicas."""
    if not math.isfinite(value) or value <= 0:
        raise ValueError(label + ' debe ser finito y positivo')
    return float(value)


def projectile(radius_model_m, density_kg_m3, speed_model_m_s, scale, mass_scale,
               max_speed_model_m_s, event_energy_j):
    """IA: Esfera de densidad explícita; mundo = modelo por escala, velocidad homóloga declarada; energía real del evento independiente, sin multiplicador artístico de masa."""
    values = [positive(v, k) for v, k in zip(
        (radius_model_m, density_kg_m3, speed_model_m_s, scale, mass_scale, max_speed_model_m_s, event_energy_j),
        ('radio','densidad','velocidad','escala','escala de masa','velocidad máxima','energía del evento'))]
    radius, density, speed, scale, mass_scale, maximum, event = values
    if speed > maximum:
        raise ValueError('La velocidad supera el límite explícito del sustituto')
    volume = 4 * math.pi * radius**3 / 3
    mass_world = volume * scale**3 * density
    speed_world = speed * scale
    energy_world = mass_world * speed_world**2 / 2
    return dict(radius_model_m=radius, density_kg_m3=density, scale=scale,
                mass_scale=mass_scale, mass_solver=volume*density*mass_scale,
                mass_world_kg=mass_world, speed_model_m_s=speed,
                speed_world_m_s=speed_world, surrogate_energy_world_j=energy_world,
                event_energy_j=event, event_to_surrogate_energy=event/energy_world,
                speed_convention='v_mundo = lambda * v_modelo; misma duración, no similitud gravitatoria')


def thin_mass(area_world_m2, thickness_world_m, density_kg_m3):
    """IA: Masa de familia fina desde área y espesor físicos de mundo explícitos; no usa el espesor de impresión."""
    return (positive(area_world_m2, 'área') * positive(thickness_world_m, 'espesor')
            * positive(density_kg_m3, 'densidad'))


def central_collision(mass_projectile, mass_target, speed, restitution):
    """IA: Referencia analítica unidimensional con blanco en reposo, sin fuerzas externas ni fractura; eta incluye solo traslación del blanco."""
    projectile_mass = positive(mass_projectile, 'masa del proyectil')
    target_mass = positive(mass_target, 'masa de la pieza')
    speed = positive(speed, 'velocidad')
    if not math.isfinite(restitution) or not 0 <= restitution <= 1:
        raise ValueError('Restitución fuera de [0,1]')
    target_speed = (1 + restitution) * speed * projectile_mass / (projectile_mass + target_mass)
    projectile_speed = (projectile_mass - restitution * target_mass) * speed / (projectile_mass + target_mass)
    return dict(target_speed=target_speed, projectile_speed=projectile_speed,
                eta=target_mass*target_speed**2/(projectile_mass*speed**2))


def dissipative_collision(mass_projectile, mass_target, speed, restitution, eta_max=.3):
    """IA: Contacto 1D con disipación interna explícita: conserva momento, reduce restitución efectiva hasta el presupuesto y rechaza límites incompatibles con separación no adhesiva."""
    baseline = central_collision(mass_projectile, mass_target, speed, restitution)
    if not math.isfinite(eta_max) or not 0 < eta_max <= 1:
        raise ValueError('Presupuesto de energía fuera de (0,1]')
    ratio = mass_target / mass_projectile
    maximum_restitution = math.sqrt(eta_max / ratio) * (1 + ratio) - 1
    if maximum_restitution < -1e-12:
        raise ValueError('El presupuesto requiere adhesión o impulso externo; no basta disipación interna')
    effective = min(restitution, max(0., maximum_restitution))
    result = central_collision(mass_projectile, mass_target, speed, effective)
    initial = .5 * mass_projectile * speed**2
    final = .5 * (mass_projectile*result['projectile_speed']**2 + mass_target*result['target_speed']**2)
    baseline_final = .5 * (mass_projectile*baseline['projectile_speed']**2 + mass_target*baseline['target_speed']**2)
    return dict(result, restitution_requested=restitution, restitution_effective=effective,
                energy_initial=initial, energy_final=final, energy_dissipated=initial-final,
                additional_dissipation=max(0., baseline_final-final), eta_max=eta_max,
                model='Disipación interna idealizada de contacto 1D; no arrastre del aire ni recorte de poses')
