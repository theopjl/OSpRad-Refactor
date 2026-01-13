"""
Workflow de Calibration d'Appareil Spectroradiométrique
=========================================================

Ce script permet de :
1. Charger et comparer deux mesures spectroradiométriques (appareil professionnel vs fait-maison)
2. Interpoler les spectres sur une grille commune avec interpolation Akima
3. Calculer des facteurs de correction (gain) pour améliorer la précision de l'appareil fait-maison
4. Visualiser les différences et générer un modèle de calibration
5. Exporter les résultats et coefficients de correction

Auteur : Workflow de calibration spectrale
Date : 13 janvier 2026
"""

import sys
from pathlib import Path
import numpy as np
from scipy.interpolate import Akima1DInterpolator
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Tuple, Optional, Dict
import json

# Configuration des chemins
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))


class SpectralCalibrator:
    """
    Classe pour calibrer un appareil spectroradiométrique fait-maison
    en utilisant les mesures d'un appareil professionnel comme référence.
    """
    
    def __init__(self):
        self.reference_wl = None
        self.reference_spectrum = None
        self.device_wl = None
        self.device_spectrum = None
        self.common_wl = None
        self.reference_interp = None
        self.device_interp = None
        self.correction_factors = None
        self.calibration_model = None
        
    def load_csv_data(self, filepath: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Charge les données d'un fichier CSV JETI.
        
        Format attendu : Wavelength, Sample1, Sample2, ..., SampleN, MeasurementType
        
        Args:
            filepath: Chemin vers le fichier CSV
            
        Returns:
            (wavelengths, mean_spectrum): Longueurs d'onde et spectre moyenné
        """
        print(f"\nChargement de : {filepath}")
        
        # Lire le fichier CSV (première ligne contient les en-têtes avec serial number)
        data = np.genfromtxt(filepath, delimiter=',', skip_header=0)
        
        # Première colonne = longueurs d'onde
        wavelengths = data[:, 0]
        
        # Colonnes 1 à N-1 = échantillons (dernière colonne = type de mesure)
        samples = data[:, 1:-1]
        
        # Calculer le spectre moyen et l'écart-type
        mean_spectrum = np.mean(samples, axis=1)
        std_spectrum = np.std(samples, axis=1)
        
        print(f"  Plage spectrale : {wavelengths[0]:.1f} - {wavelengths[-1]:.1f} nm")
        print(f"  Nombre de points : {len(wavelengths)}")
        print(f"  Nombre d'échantillons : {samples.shape[1]}")
        print(f"  Valeur moyenne : {np.mean(mean_spectrum):.3e}")
        print(f"  Écart-type moyen : {np.mean(std_spectrum):.3e}")
        
        return wavelengths, mean_spectrum
    
    def load_reference_data(self, filepath: str):
        """Charge les données de l'appareil de référence (professionnel)."""
        self.reference_wl, self.reference_spectrum = self.load_csv_data(filepath)
        print(f"✓ Données de référence chargées")
    
    def load_device_data(self, filepath: str):
        """Charge les données de l'appareil fait-maison."""
        self.device_wl, self.device_spectrum = self.load_csv_data(filepath)
        print(f"✓ Données de l'appareil chargées")
    
    def interpolate_to_common_grid(self, step: float = 1.0):
        """
        Interpole les deux spectres sur une grille commune avec interpolation Akima.
        
        L'interpolation Akima est préférable pour les données spectrales car :
        - Pas d'oscillations (overshoot) contrairement aux splines cubiques
        - Lisse et continue
        - Localisée : les modifications d'un point n'affectent pas tout le spectre
        
        Args:
            step: Pas d'échantillonnage en nm (défaut: 1.0 nm)
        """
        if self.reference_wl is None or self.device_wl is None:
            raise ValueError("Veuillez d'abord charger les données de référence et de l'appareil")
        
        print(f"\n{'='*70}")
        print("INTERPOLATION SUR GRILLE COMMUNE (Akima)")
        print(f"{'='*70}")
        
        # Déterminer la plage commune
        wl_min = max(self.reference_wl[0], self.device_wl[0])
        wl_max = min(self.reference_wl[-1], self.device_wl[-1])
        
        print(f"Plage commune : {wl_min:.1f} - {wl_max:.1f} nm")
        print(f"Pas d'échantillonnage : {step} nm")
        
        # Créer la grille commune
        self.common_wl = np.arange(wl_min, wl_max + step/2, step)
        print(f"Nombre de points interpolés : {len(self.common_wl)}")
        
        # Interpolation Akima pour la référence
        print("\nInterpolation de la référence...")
        akima_ref = Akima1DInterpolator(self.reference_wl, self.reference_spectrum)
        self.reference_interp = akima_ref(self.common_wl)
        
        # Interpolation Akima pour l'appareil
        print("Interpolation de l'appareil...")
        akima_device = Akima1DInterpolator(self.device_wl, self.device_spectrum)
        self.device_interp = akima_device(self.common_wl)
        
        print("✓ Interpolation terminée")
        
        # Statistiques sur les données interpolées
        print(f"\nRéférence interpolée :")
        print(f"  Min : {np.min(self.reference_interp):.3e}")
        print(f"  Max : {np.max(self.reference_interp):.3e}")
        print(f"  Moyenne : {np.mean(self.reference_interp):.3e}")
        
        print(f"\nAppareil interpolé :")
        print(f"  Min : {np.min(self.device_interp):.3e}")
        print(f"  Max : {np.max(self.device_interp):.3e}")
        print(f"  Moyenne : {np.mean(self.device_interp):.3e}")
    
    def calculate_correction_factors(self, method: str = 'ratio'):
        """
        Calcule les facteurs de correction pour calibrer l'appareil fait-maison.
        
        Args:
            method: Méthode de calcul
                - 'ratio': Rapport simple (référence / appareil)
                - 'polynomial': Ajustement polynomial
                - 'adaptive': Correction adaptative par bandes spectrales
        """
        if self.reference_interp is None or self.device_interp is None:
            raise ValueError("Veuillez d'abord interpoler les données")
        
        print(f"\n{'='*70}")
        print(f"CALCUL DES FACTEURS DE CORRECTION (méthode: {method})")
        print(f"{'='*70}")
        
        # Éviter division par zéro
        epsilon = 1e-10
        
        if method == 'ratio':
            # Facteur de correction simple : ratio référence / appareil
            self.correction_factors = self.reference_interp / (self.device_interp + epsilon)
            
            print(f"\nFacteurs de correction (ratio) :")
            print(f"  Min : {np.min(self.correction_factors):.4f}")
            print(f"  Max : {np.max(self.correction_factors):.4f}")
            print(f"  Moyenne : {np.mean(self.correction_factors):.4f}")
            print(f"  Médiane : {np.median(self.correction_factors):.4f}")
            print(f"  Écart-type : {np.std(self.correction_factors):.4f}")
            
            # Détecter les anomalies (facteurs trop éloignés de la médiane)
            median = np.median(self.correction_factors)
            mad = np.median(np.abs(self.correction_factors - median))
            outliers = np.abs(self.correction_factors - median) > 3 * mad
            
            if np.any(outliers):
                print(f"\n⚠️  {np.sum(outliers)} points aberrants détectés")
                print(f"    (facteur > 3×MAD de la médiane)")
        
        elif method == 'polynomial':
            # Ajustement polynomial du rapport
            degree = 5
            coeffs = np.polyfit(self.common_wl, 
                               self.reference_interp / (self.device_interp + epsilon),
                               degree)
            self.correction_factors = np.polyval(coeffs, self.common_wl)
            
            print(f"\nAjustement polynomial (degré {degree}) :")
            print(f"  Coefficients : {coeffs}")
            self.calibration_model = {'type': 'polynomial', 'degree': degree, 'coeffs': coeffs.tolist()}
        
        elif method == 'adaptive':
            # Correction adaptative par bandes spectrales
            bands = [
                (380, 450, "UV-Bleu"),
                (450, 550, "Vert"),
                (550, 650, "Jaune-Rouge"),
                (650, 780, "Rouge-IR")
            ]
            
            self.correction_factors = np.zeros_like(self.reference_interp)
            print(f"\nCorrection par bandes spectrales :")
            
            for wl_min, wl_max, name in bands:
                mask = (self.common_wl >= wl_min) & (self.common_wl <= wl_max)
                if np.any(mask):
                    ratio = self.reference_interp[mask] / (self.device_interp[mask] + epsilon)
                    factor = np.median(ratio)  # Utiliser la médiane pour robustesse
                    self.correction_factors[mask] = factor
                    print(f"  {name:15s} ({wl_min}-{wl_max} nm) : facteur = {factor:.4f}")
        
        else:
            raise ValueError(f"Méthode '{method}' non reconnue")
        
        print("✓ Facteurs de correction calculés")
    
    def apply_correction(self) -> np.ndarray:
        """
        Applique les facteurs de correction au spectre de l'appareil.
        
        Returns:
            Spectre corrigé
        """
        if self.correction_factors is None:
            raise ValueError("Veuillez d'abord calculer les facteurs de correction")
        
        corrected_spectrum = self.device_interp * self.correction_factors
        
        print(f"\n{'='*70}")
        print("APPLICATION DE LA CORRECTION")
        print(f"{'='*70}")
        print(f"Spectre corrigé :")
        print(f"  Min : {np.min(corrected_spectrum):.3e}")
        print(f"  Max : {np.max(corrected_spectrum):.3e}")
        print(f"  Moyenne : {np.mean(corrected_spectrum):.3e}")
        
        return corrected_spectrum
    
    def evaluate_correction(self, corrected_spectrum: np.ndarray) -> Dict:
        """
        Évalue la qualité de la correction.
        
        Args:
            corrected_spectrum: Spectre corrigé
            
        Returns:
            Dictionnaire de métriques de qualité
        """
        print(f"\n{'='*70}")
        print("ÉVALUATION DE LA CORRECTION")
        print(f"{'='*70}")
        
        # Avant correction
        diff_before = self.device_interp - self.reference_interp
        rmse_before = np.sqrt(np.mean(diff_before**2))
        mae_before = np.mean(np.abs(diff_before))
        corr_before = np.corrcoef(self.device_interp, self.reference_interp)[0, 1]
        
        # Après correction
        diff_after = corrected_spectrum - self.reference_interp
        rmse_after = np.sqrt(np.mean(diff_after**2))
        mae_after = np.mean(np.abs(diff_after))
        corr_after = np.corrcoef(corrected_spectrum, self.reference_interp)[0, 1]
        
        # Amélioration relative
        rmse_improvement = (rmse_before - rmse_after) / rmse_before * 100
        mae_improvement = (mae_before - mae_after) / mae_before * 100
        
        print("\nAvant correction :")
        print(f"  RMSE : {rmse_before:.3e}")
        print(f"  MAE  : {mae_before:.3e}")
        print(f"  Corrélation : {corr_before:.6f}")
        
        print("\nAprès correction :")
        print(f"  RMSE : {rmse_after:.3e}")
        print(f"  MAE  : {mae_after:.3e}")
        print(f"  Corrélation : {corr_after:.6f}")
        
        print("\nAmélioration :")
        print(f"  RMSE : {rmse_improvement:+.2f}%")
        print(f"  MAE  : {mae_improvement:+.2f}%")
        
        metrics = {
            'rmse_before': rmse_before,
            'rmse_after': rmse_after,
            'mae_before': mae_before,
            'mae_after': mae_after,
            'correlation_before': corr_before,
            'correlation_after': corr_after,
            'rmse_improvement_percent': rmse_improvement,
            'mae_improvement_percent': mae_improvement
        }
        
        return metrics
    
    def plot_comparison(self, corrected_spectrum: np.ndarray, save_path: Optional[str] = None):
        """
        Génère des graphiques de comparaison.
        
        Args:
            corrected_spectrum: Spectre corrigé
            save_path: Chemin pour sauvegarder le graphique (optionnel)
        """
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Calibration Spectroradiométrique', fontsize=16, fontweight='bold')
        
        # 1. Comparaison des spectres
        ax = axes[0, 0]
        ax.plot(self.common_wl, self.reference_interp, 'b-', linewidth=2, label='Référence (Pro)')
        ax.plot(self.common_wl, self.device_interp, 'r--', linewidth=1.5, label='Appareil (Avant)')
        ax.plot(self.common_wl, corrected_spectrum, 'g-', linewidth=1.5, alpha=0.7, label='Appareil (Après)')
        ax.set_xlabel('Longueur d\'onde (nm)')
        ax.set_ylabel('Irradiance (W/m²/nm)')
        ax.set_title('Comparaison des Spectres')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Facteurs de correction
        ax = axes[0, 1]
        ax.plot(self.common_wl, self.correction_factors, 'purple', linewidth=2)
        ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Facteur = 1')
        ax.axhline(y=np.median(self.correction_factors), color='orange', 
                   linestyle='--', alpha=0.7, label=f'Médiane = {np.median(self.correction_factors):.3f}')
        ax.set_xlabel('Longueur d\'onde (nm)')
        ax.set_ylabel('Facteur de correction')
        ax.set_title('Facteurs de Correction Spectraux')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. Erreurs absolues
        ax = axes[1, 0]
        error_before = np.abs(self.device_interp - self.reference_interp)
        error_after = np.abs(corrected_spectrum - self.reference_interp)
        ax.plot(self.common_wl, error_before, 'r-', linewidth=1.5, alpha=0.7, label='Avant correction')
        ax.plot(self.common_wl, error_after, 'g-', linewidth=1.5, alpha=0.7, label='Après correction')
        ax.set_xlabel('Longueur d\'onde (nm)')
        ax.set_ylabel('Erreur absolue (W/m²/nm)')
        ax.set_title('Erreurs Absolues')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        
        # 4. Erreurs relatives (%)
        ax = axes[1, 1]
        rel_error_before = (error_before / (self.reference_interp + 1e-10)) * 100
        rel_error_after = (error_after / (self.reference_interp + 1e-10)) * 100
        ax.plot(self.common_wl, rel_error_before, 'r-', linewidth=1.5, alpha=0.7, label='Avant correction')
        ax.plot(self.common_wl, rel_error_after, 'g-', linewidth=1.5, alpha=0.7, label='Après correction')
        ax.set_xlabel('Longueur d\'onde (nm)')
        ax.set_ylabel('Erreur relative (%)')
        ax.set_title('Erreurs Relatives')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, min(np.percentile(rel_error_before, 95), 100)])
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"\n✓ Graphique sauvegardé : {save_path}")
        else:
            plt.show()
    
    def export_calibration(self, output_dir: str, prefix: str = "calibration"):
        """
        Exporte les résultats de calibration.
        
        Args:
            output_dir: Répertoire de sortie
            prefix: Préfixe des fichiers de sortie
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n{'='*70}")
        print("EXPORT DES RÉSULTATS")
        print(f"{'='*70}")
        
        # 1. Exporter les facteurs de correction
        correction_file = output_path / f"{prefix}_factors_{timestamp}.txt"
        data = np.column_stack((self.common_wl, self.correction_factors))
        header = f"""Facteurs de Correction Spectrale
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Plage : {self.common_wl[0]:.1f} - {self.common_wl[-1]:.1f} nm
Points : {len(self.common_wl)}

Format : Wavelength(nm)  CorrectionFactor"""
        
        np.savetxt(correction_file, data, fmt='%.6f %.6f', header=header)
        print(f"✓ Facteurs de correction : {correction_file}")
        
        # 2. Exporter le spectre corrigé
        corrected_spectrum = self.apply_correction()
        corrected_file = output_path / f"{prefix}_corrected_spectrum_{timestamp}.txt"
        data = np.column_stack((self.common_wl, corrected_spectrum))
        header = f"""Spectre Corrigé
Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Plage : {self.common_wl[0]:.1f} - {self.common_wl[-1]:.1f} nm

Format : Wavelength(nm)  Irradiance(W/m²/nm)"""
        
        np.savetxt(corrected_file, data, fmt='%.6f %.6e', header=header)
        print(f"✓ Spectre corrigé : {corrected_file}")
        
        # 3. Exporter les métriques
        metrics = self.evaluate_correction(corrected_spectrum)
        metrics_file = output_path / f"{prefix}_metrics_{timestamp}.json"
        
        metrics_data = {
            'timestamp': timestamp,
            'wavelength_range': [float(self.common_wl[0]), float(self.common_wl[-1])],
            'num_points': int(len(self.common_wl)),
            'correction_factor_stats': {
                'min': float(np.min(self.correction_factors)),
                'max': float(np.max(self.correction_factors)),
                'mean': float(np.mean(self.correction_factors)),
                'median': float(np.median(self.correction_factors)),
                'std': float(np.std(self.correction_factors))
            },
            'quality_metrics': {k: float(v) for k, v in metrics.items()}
        }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Métriques : {metrics_file}")
        
        # 4. Exporter le graphique
        plot_file = output_path / f"{prefix}_comparison_{timestamp}.png"
        self.plot_comparison(corrected_spectrum, save_path=str(plot_file))
        
        print(f"\n✓ Tous les fichiers exportés dans : {output_path}")
        
        return corrected_spectrum, metrics


def main_interactive():
    """
    Workflow interactif de calibration.
    """
    print("="*70)
    print(" WORKFLOW DE CALIBRATION SPECTRORADIOMÉTRIQUE")
    print("="*70)
    print("\nCe script permet de calibrer un appareil fait-maison en utilisant")
    print("les mesures d'un appareil professionnel comme référence.\n")
    
    # Initialiser le calibrateur
    calibrator = SpectralCalibrator()
    
    # Demander les fichiers d'entrée
    print("\n" + "-"*70)
    print("ÉTAPE 1 : Chargement des données")
    print("-"*70)
    
    # Par défaut, utiliser les fichiers du dossier reports
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    
    # Lister les fichiers CSV disponibles
    csv_files = sorted(list(reports_dir.glob("*.csv")))
    
    if not csv_files:
        print(f"\n❌ Aucun fichier CSV trouvé dans {reports_dir}")
        return
    
    print("\nFichiers CSV disponibles :")
    for i, f in enumerate(csv_files, 1):
        print(f"  {i}. {f.name}")
    
    # Sélection du fichier de référence
    while True:
        choice = input("\nChoisir le numéro du fichier de référence (professionnel) : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
            ref_file = str(csv_files[int(choice)-1])
            break
        else:
            print(f"❌ Choix invalide. Veuillez entrer un nombre entre 1 et {len(csv_files)}")
    
    # Sélection du fichier de l'appareil fait-maison
    while True:
        choice = input("\nChoisir le numéro du fichier de l'appareil fait-maison : ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
            device_file = str(csv_files[int(choice)-1])
            break
        else:
            print(f"❌ Choix invalide. Veuillez entrer un nombre entre 1 et {len(csv_files)}")
    
    # Charger les données
    try:
        calibrator.load_reference_data(ref_file)
        calibrator.load_device_data(device_file)
    except Exception as e:
        print(f"\n❌ Erreur lors du chargement : {e}")
        return
    
    # Interpolation
    print("\n" + "-"*70)
    print("ÉTAPE 2 : Interpolation sur grille commune")
    print("-"*70)
    
    step = input("\nPas d'échantillonnage (nm) [1.0] : ").strip()
    step = float(step) if step else 1.0
    
    calibrator.interpolate_to_common_grid(step=step)
    
    # Calcul des facteurs de correction
    print("\n" + "-"*70)
    print("ÉTAPE 3 : Calcul des facteurs de correction")
    print("-"*70)
    
    print("\nMéthodes disponibles :")
    print("  1. ratio      - Rapport simple (recommandé)")
    print("  2. polynomial - Ajustement polynomial")
    print("  3. adaptive   - Correction par bandes spectrales")
    
    method_choice = input("\nChoisir la méthode [1] : ").strip()
    method_map = {'1': 'ratio', '2': 'polynomial', '3': 'adaptive'}
    method = method_map.get(method_choice, 'ratio')
    
    calibrator.calculate_correction_factors(method=method)
    
    # Application et évaluation
    corrected_spectrum = calibrator.apply_correction()
    metrics = calibrator.evaluate_correction(corrected_spectrum)
    
    # Export
    print("\n" + "-"*70)
    print("ÉTAPE 4 : Export des résultats")
    print("-"*70)
    
    output_dir = input(f"\nRépertoire de sortie [{reports_dir}] : ").strip()
    if not output_dir:
        output_dir = str(reports_dir)
    
    calibrator.export_calibration(output_dir, prefix="calibration")
    
    print("\n" + "="*70)
    print(" CALIBRATION TERMINÉE !")
    print("="*70)
    print("\nVous pouvez maintenant utiliser les facteurs de correction")
    print("pour améliorer les mesures futures de votre appareil fait-maison.")
    print("\nConseil : Multipliez vos mesures brutes par les facteurs de")
    print("          correction correspondant à chaque longueur d'onde.")


if __name__ == "__main__":
    main_interactive()
