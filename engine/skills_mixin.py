# ============================================================
# engine/skills_mixin.py
# Mixin con toda la lógica de skills, XP y especialidades.
# Extraído de personaje.py para reducir su tamaño.
# ============================================================
from __future__ import annotations

from data.skills import SKILLS


class SkillsMixin:
    """Métodos de skills para Sobreviviente (mixin)."""

    def _derivar_skills(self) -> dict[str, int]:
        derivados: dict[str, int] = {}
        for skill_key, defn in SKILLS.items():
            pesos = defn.get("derivacion", [])
            if not pesos:
                derivados[skill_key] = 0
                continue

            suma_pesos = max(1, sum(m for _, m in pesos))
            promedio = sum(self.stats.get(stat, 0) * mult for stat, mult in pesos) / suma_pesos

            # Escala inicial deliberadamente conservadora para evitar personajes
            # de arranque en rango experto/legendario.
            valor = int(promedio * 4)
            derivados[skill_key] = max(0, min(defn.get("max", 100), valor))
        return derivados

    # ─────────────────────────────────────────────────────────
    #  XP
    # ─────────────────────────────────────────────────────────

    def ganar_xp_skill(self, skill_key: str, xp_base: int) -> None:
        if skill_key not in self.skills:
            return
        defn  = SKILLS.get(skill_key, {})
        s_max = defn.get("max", 100)
        if self.skills[skill_key] >= s_max:
            return
        mult = self.obtener_efecto_rasgo("xp_mult_global", 1.0)
        self.skills_xp[skill_key] = self.skills_xp.get(skill_key, 0) + max(1, int(xp_base * mult))
        while self.skills[skill_key] < s_max:
            nivel = self.skills[skill_key]
            xp_need = self.xp_necesaria_skill(skill_key)
            if self.skills_xp[skill_key] >= xp_need:
                self.skills_xp[skill_key] -= xp_need
                self.skills[skill_key]    += 1
                self._progreso_skills_pendiente.append(
                    f"{defn.get('icono','📈')} {defn['nombre']}  {nivel} → {nivel+1}"
                )
                nuevas = self._desbloquear_especialidades(skill_key)
                for esp in nuevas:
                    self._progreso_skills_pendiente.append(
                        f"★ {defn['nombre']}: especialidad desbloqueada -> {esp}"
                    )
            else:
                break
        if self._progreso_skills_pendiente:
            self.evaluar_rasgos_nuevos()

    def recoger_progreso_skills(self) -> list[str]:
        msgs = self._progreso_skills_pendiente.copy()
        self._progreso_skills_pendiente.clear()
        return msgs

    def xp_necesaria_skill(self, skill_key: str) -> int:
        defn = SKILLS.get(skill_key, {})
        nivel = self.skills.get(skill_key, 0)
        base = int(defn.get("xp_base", 10))
        incr = int(defn.get("xp_incremento", 5))
        factor = float(defn.get("growth_factor", 0.10))
        progresiva = int((nivel ** 1.16) * factor)
        return max(1, base + (nivel // 10) * incr + progresiva)

    def nivel_maestria_skill(self, skill_key: str) -> str:
        n = self.skills.get(skill_key, 0)
        if n >= 90:
            return "Legendario"
        if n >= 75:
            return "Experto"
        if n >= 55:
            return "Avanzado"
        if n >= 35:
            return "Competente"
        if n >= 15:
            return "Basico"
        return "Novato"

    def especialidades_skill(self, skill_key: str) -> list[str]:
        return list(self.especialidades_desbloqueadas.get(skill_key, []))

    def _desbloquear_especialidades(self, skill_key: str) -> list[str]:
        defn = SKILLS.get(skill_key, {})
        nivel = self.skills.get(skill_key, 0)
        desbloqueadas = self.especialidades_desbloqueadas.setdefault(skill_key, [])
        nuevas: list[str] = []
        for esp in defn.get("especialidades", []):
            nombre = str(esp.get("nombre", "")).strip()
            if not nombre:
                continue
            if nivel >= int(esp.get("nivel_req", 999)) and nombre not in desbloqueadas:
                desbloqueadas.append(nombre)
                nuevas.append(nombre)
        return nuevas

    def _recalcular_especialidades(self) -> None:
        self.especialidades_desbloqueadas = {
            k: list(self.especialidades_desbloqueadas.get(k, []))
            for k in self.skills
        }
        for skill_key in self.skills:
            self._desbloquear_especialidades(skill_key)

    def bonus_especialidades(self, skill_key: str, contexto: str = "") -> int:
        if skill_key not in SKILLS:
            return 0
        contexto_l = (contexto or "").lower()
        desbloqueadas = set(self.especialidades_desbloqueadas.get(skill_key, []))
        bonus = 0
        for esp in SKILLS[skill_key].get("especialidades", []):
            nombre = str(esp.get("nombre", "")).strip()
            if not nombre or nombre not in desbloqueadas:
                continue
            ctx = [str(c).lower() for c in esp.get("contextos", [])]
            if not ctx or any(c in contexto_l for c in ctx):
                bonus += int(esp.get("bonus_check", 0))
        return bonus
