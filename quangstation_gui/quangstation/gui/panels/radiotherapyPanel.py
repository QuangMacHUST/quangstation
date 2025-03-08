import logging
from typing import Dict, List, Optional, Union

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                           QComboBox, QPushButton, QSpinBox, QDoubleSpinBox,
                           QGroupBox, QTabWidget, QMessageBox, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSlot

from quangstation.core.data import ROIContour, ROIMask, PatientList
from quangstation.core.data.images import CTImage, DoseImage
from quangstation.core.data.plan import RTPlan
from quangstation.core.processing.radiotherapyTechniques import ThreeDCRT, VMAT, SRS, SBRT

logger = logging.getLogger(__name__)

class RadiotherapyPanel(QWidget):
    """
    Panel for creating and managing advanced radiotherapy treatment plans.
    Includes support for 3DCRT, VMAT, SRS, and SBRT techniques.
    """
    
    def __init__(self, viewController):
        super().__init__()
        self._viewController = viewController
        
        # Create technique instances
        self._techniques = {
            "3DCRT": ThreeDCRT(),
            "VMAT": VMAT(),
            "SRS": SRS(),
            "SBRT": SBRT()
        }
        
        # Current selections
        self._selected_technique = None
        self._selected_targets = []
        self._selected_oars = []
        self._prescriptions = {}
        
        self._setupUI()
        self._connectSignals()
        
    def _setupUI(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Technique selection
        technique_group = QGroupBox("Treatment Technique")
        technique_layout = QVBoxLayout()
        technique_group.setLayout(technique_layout)
        
        self._technique_combo = QComboBox()
        self._technique_combo.addItems(list(self._techniques.keys()))
        technique_layout.addWidget(self._technique_combo)
        
        main_layout.addWidget(technique_group)
        
        # Targets and OARs selection
        selection_tabs = QTabWidget()
        
        # Targets tab
        targets_widget = QWidget()
        targets_layout = QVBoxLayout()
        targets_widget.setLayout(targets_layout)
        
        # Available structures
        targets_label = QLabel("Available structures:")
        targets_layout.addWidget(targets_label)
        
        self._structures_combo = QComboBox()
        targets_layout.addWidget(self._structures_combo)
        
        self._add_target_btn = QPushButton("Add as Target")
        targets_layout.addWidget(self._add_target_btn)
        
        # Selected targets
        selected_targets_label = QLabel("Selected targets:")
        targets_layout.addWidget(selected_targets_label)
        
        self._targets_list_widget = QWidget()
        self._targets_list_layout = QVBoxLayout()
        self._targets_list_layout.setAlignment(Qt.AlignTop)
        self._targets_list_widget.setLayout(self._targets_list_layout)
        
        targets_layout.addWidget(self._targets_list_widget)
        
        selection_tabs.addTab(targets_widget, "Targets")
        
        # OARs tab
        oars_widget = QWidget()
        oars_layout = QVBoxLayout()
        oars_widget.setLayout(oars_layout)
        
        # Available structures (reused from targets)
        oars_label = QLabel("Available structures:")
        oars_layout.addWidget(oars_label)
        
        self._oar_structures_combo = QComboBox()
        oars_layout.addWidget(self._oar_structures_combo)
        
        self._add_oar_btn = QPushButton("Add as OAR")
        oars_layout.addWidget(self._add_oar_btn)
        
        # Selected OARs
        selected_oars_label = QLabel("Selected OARs:")
        oars_layout.addWidget(selected_oars_label)
        
        self._oars_list_widget = QWidget()
        self._oars_list_layout = QVBoxLayout()
        self._oars_list_layout.setAlignment(Qt.AlignTop)
        self._oars_list_widget.setLayout(self._oars_list_layout)
        
        oars_layout.addWidget(self._oars_list_widget)
        
        selection_tabs.addTab(oars_widget, "OARs")
        
        main_layout.addWidget(selection_tabs)
        
        # Technique-specific parameters
        self._parameters_group = QGroupBox("Technique Parameters")
        self._parameters_layout = QVBoxLayout()
        self._parameters_group.setLayout(self._parameters_layout)
        
        main_layout.addWidget(self._parameters_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self._create_plan_btn = QPushButton("Create Plan")
        self._create_plan_btn.setEnabled(False)
        actions_layout.addWidget(self._create_plan_btn)
        
        self._optimize_plan_btn = QPushButton("Optimize Plan")
        self._optimize_plan_btn.setEnabled(False)
        actions_layout.addWidget(self._optimize_plan_btn)
        
        self._calculate_dose_btn = QPushButton("Calculate Dose")
        self._calculate_dose_btn.setEnabled(False)
        actions_layout.addWidget(self._calculate_dose_btn)
        
        main_layout.addLayout(actions_layout)
        
        # Update UI with current patient data
        self._updateStructuresCombos()
        self._updateTechniqueParameters()
        
    def _connectSignals(self):
        """Connect all signals to slots"""
        # Technique selection
        self._technique_combo.currentTextChanged.connect(self._onTechniqueChanged)
        
        # Structure selection
        self._add_target_btn.clicked.connect(self._onAddTarget)
        self._add_oar_btn.clicked.connect(self._onAddOAR)
        
        # Plan actions
        self._create_plan_btn.clicked.connect(self._onCreatePlan)
        self._optimize_plan_btn.clicked.connect(self._onOptimizePlan)
        self._calculate_dose_btn.clicked.connect(self._onCalculateDose)
        
        # Connect to patient/CT changes to update available structures
        self._viewController.selectedImageChangedSignal.connect(self._onSelectedImageChanged)
        
        # Connect to technique signals
        for technique in self._techniques.values():
            technique.planCreatedSignal.connect(self._onPlanCreated)
            technique.planUpdatedSignal.connect(self._onPlanUpdated)
            technique.computationProgressSignal.connect(self._onComputationProgress)
    
    def _updateStructuresCombos(self):
        """Update the structures comboboxes with current patient data"""
        self._structures_combo.clear()
        self._oar_structures_combo.clear()
        
        patient = self._viewController.currentPatient
        if not patient:
            return
        
        # Add ROI contours
        for roi in patient.dataDict.get('ROIContours', []):
            self._structures_combo.addItem(roi.name, roi)
            self._oar_structures_combo.addItem(roi.name, roi)
        
        # Add ROI masks
        for roi in patient.dataDict.get('ROIMasks', []):
            self._structures_combo.addItem(roi.name, roi)
            self._oar_structures_combo.addItem(roi.name, roi)
        
        # Update create plan button state
        self._updateCreatePlanButtonState()
    
    def _clearParametersLayout(self):
        """Clear all widgets from parameters layout"""
        while self._parameters_layout.count():
            item = self._parameters_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _updateTechniqueParameters(self):
        """Update the parameters section based on selected technique"""
        self._clearParametersLayout()
        
        technique_name = self._technique_combo.currentText()
        if not technique_name or technique_name not in self._techniques:
            return
        
        technique = self._techniques[technique_name]
        self._selected_technique = technique
        
        # Common parameters
        common_group = QGroupBox("Common Parameters")
        common_layout = QGridLayout()
        common_group.setLayout(common_layout)
        
        # Number of fractions
        fractions_label = QLabel("Number of fractions:")
        common_layout.addWidget(fractions_label, 0, 0)
        
        self._fractions_spin = QSpinBox()
        self._fractions_spin.setRange(1, 40)
        self._fractions_spin.setValue(technique_name == "SRS" and 1 or technique_name == "SBRT" and 5 or 30)
        common_layout.addWidget(self._fractions_spin, 0, 1)
        
        # Plan name
        plan_name_label = QLabel("Plan name:")
        common_layout.addWidget(plan_name_label, 1, 0)
        
        self._plan_name_edit = QLineEdit(f"{technique_name} Plan")
        common_layout.addWidget(self._plan_name_edit, 1, 1)
        
        self._parameters_layout.addWidget(common_group)
        
        # Technique-specific parameters
        if technique_name == "3DCRT":
            self._setup3DCRTParameters(technique)
        elif technique_name == "VMAT":
            self._setupVMATParameters(technique)
        elif technique_name == "SRS":
            self._setupSRSParameters(technique)
        elif technique_name == "SBRT":
            self._setupSBRTParameters(technique)
    
    def _setup3DCRTParameters(self, technique):
        """Set up parameters specific to 3DCRT"""
        group = QGroupBox("3DCRT Parameters")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Number of beams
        beams_label = QLabel("Number of beams:")
        layout.addWidget(beams_label, 0, 0)
        
        self._beams_spin = QSpinBox()
        self._beams_spin.setRange(1, 12)
        self._beams_spin.setValue(technique.num_beams)
        layout.addWidget(self._beams_spin, 0, 1)
        
        # Beam energy
        energy_label = QLabel("Beam energy (MV):")
        layout.addWidget(energy_label, 1, 0)
        
        self._energy_combo = QComboBox()
        self._energy_combo.addItems(["6", "10", "15", "18", "23"])
        self._energy_combo.setCurrentText(str(int(technique.beam_energy)))
        layout.addWidget(self._energy_combo, 1, 1)
        
        self._parameters_layout.addWidget(group)
    
    def _setupVMATParameters(self, technique):
        """Set up parameters specific to VMAT"""
        group = QGroupBox("VMAT Parameters")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Number of arcs
        arcs_label = QLabel("Number of arcs:")
        layout.addWidget(arcs_label, 0, 0)
        
        self._arcs_spin = QSpinBox()
        self._arcs_spin.setRange(1, 4)
        self._arcs_spin.setValue(technique.num_arcs)
        layout.addWidget(self._arcs_spin, 0, 1)
        
        # Beam energy
        energy_label = QLabel("Beam energy (MV):")
        layout.addWidget(energy_label, 1, 0)
        
        self._energy_combo = QComboBox()
        self._energy_combo.addItems(["6", "10", "15", "18", "23"])
        self._energy_combo.setCurrentText(str(int(technique.beam_energy)))
        layout.addWidget(self._energy_combo, 1, 1)
        
        # Control points
        cp_label = QLabel("Control points per arc:")
        layout.addWidget(cp_label, 2, 0)
        
        self._cp_spin = QSpinBox()
        self._cp_spin.setRange(10, 180)
        self._cp_spin.setValue(technique.control_points_per_arc)
        layout.addWidget(self._cp_spin, 2, 1)
        
        self._parameters_layout.addWidget(group)
    
    def _setupSRSParameters(self, technique):
        """Set up parameters specific to SRS"""
        group = QGroupBox("SRS Parameters")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Number of arcs
        arcs_label = QLabel("Number of arcs:")
        layout.addWidget(arcs_label, 0, 0)
        
        self._arcs_spin = QSpinBox()
        self._arcs_spin.setRange(1, 5)
        self._arcs_spin.setValue(technique.num_arcs)
        layout.addWidget(self._arcs_spin, 0, 1)
        
        # Beam energy
        energy_label = QLabel("Beam energy (MV):")
        layout.addWidget(energy_label, 1, 0)
        
        self._energy_combo = QComboBox()
        self._energy_combo.addItems(["6", "10", "15", "18", "23"])
        self._energy_combo.setCurrentText(str(int(technique.beam_energy)))
        layout.addWidget(self._energy_combo, 1, 1)
        
        # Non-coplanar beams
        noncoplanar_label = QLabel("Use non-coplanar beams:")
        layout.addWidget(noncoplanar_label, 2, 0)
        
        self._noncoplanar_check = QCheckBox()
        self._noncoplanar_check.setChecked(any(angle != 0 for angle in technique.couch_angles))
        layout.addWidget(self._noncoplanar_check, 2, 1)
        
        self._parameters_layout.addWidget(group)
    
    def _setupSBRTParameters(self, technique):
        """Set up parameters specific to SBRT"""
        group = QGroupBox("SBRT Parameters")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Number of fractions
        fractions_label = QLabel("Number of fractions:")
        layout.addWidget(fractions_label, 0, 0)
        
        self._sbrt_fractions_spin = QSpinBox()
        self._sbrt_fractions_spin.setRange(1, 10)
        self._sbrt_fractions_spin.setValue(technique.num_fractions)
        layout.addWidget(self._sbrt_fractions_spin, 0, 1)
        
        # Number of arcs
        arcs_label = QLabel("Number of arcs:")
        layout.addWidget(arcs_label, 1, 0)
        
        self._arcs_spin = QSpinBox()
        self._arcs_spin.setRange(1, 5)
        self._arcs_spin.setValue(technique.num_arcs)
        layout.addWidget(self._arcs_spin, 1, 1)
        
        # Beam energy
        energy_label = QLabel("Beam energy (MV):")
        layout.addWidget(energy_label, 2, 0)
        
        self._energy_combo = QComboBox()
        self._energy_combo.addItems(["6", "10", "15", "18", "23"])
        self._energy_combo.setCurrentText(str(int(technique.beam_energy)))
        layout.addWidget(self._energy_combo, 2, 1)
        
        # Non-coplanar beams
        noncoplanar_label = QLabel("Use non-coplanar beams:")
        layout.addWidget(noncoplanar_label, 3, 0)
        
        self._noncoplanar_check = QCheckBox()
        self._noncoplanar_check.setChecked(any(angle != 0 for angle in technique.couch_angles))
        layout.addWidget(self._noncoplanar_check, 3, 1)
        
        self._parameters_layout.addWidget(group)
    
    def _onTechniqueChanged(self, technique_name):
        """Handler for technique selection changes"""
        self._updateTechniqueParameters()
    
    def _onAddTarget(self):
        """Add a selected structure as a target"""
        if self._structures_combo.count() == 0:
            return
        
        structure = self._structures_combo.currentData()
        if not structure:
            return
        
        # Avoid duplicates
        for target in self._selected_targets:
            if target.name == structure.name:
                QMessageBox.warning(self, "Duplicate Target", 
                                  f"Structure '{structure.name}' is already added as a target.")
                return
        
        # Add to selected targets
        self._selected_targets.append(structure)
        
        # Create target list item with prescription
        target_widget = QWidget()
        target_layout = QHBoxLayout()
        target_widget.setLayout(target_layout)
        
        # Target name
        target_label = QLabel(structure.name)
        target_layout.addWidget(target_label)
        
        # Prescription dose
        dose_label = QLabel("Prescription:")
        target_layout.addWidget(dose_label)
        
        dose_spin = QDoubleSpinBox()
        dose_spin.setRange(0.1, 80)
        dose_spin.setValue(2.0)  # Default prescription
        dose_spin.setSuffix(" Gy")
        target_layout.addWidget(dose_spin)
        
        # Store prescription
        self._prescriptions[structure.name] = dose_spin
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedWidth(70)
        remove_btn.clicked.connect(lambda: self._removeTarget(structure, target_widget))
        target_layout.addWidget(remove_btn)
        
        # Add to the targets list
        self._targets_list_layout.addWidget(target_widget)
        
        # Update create plan button state
        self._updateCreatePlanButtonState()
    
    def _removeTarget(self, structure, widget):
        """Remove a target from the selected targets list"""
        # Remove from selected targets
        self._selected_targets = [t for t in self._selected_targets if t.name != structure.name]
        
        # Remove prescription
        if structure.name in self._prescriptions:
            del self._prescriptions[structure.name]
        
        # Remove from UI
        widget.setParent(None)
        widget.deleteLater()
        
        # Update create plan button state
        self._updateCreatePlanButtonState()
    
    def _onAddOAR(self):
        """Add a selected structure as an OAR"""
        if self._oar_structures_combo.count() == 0:
            return
        
        structure = self._oar_structures_combo.currentData()
        if not structure:
            return
        
        # Avoid duplicates
        for oar in self._selected_oars:
            if oar.name == structure.name:
                QMessageBox.warning(self, "Duplicate OAR", 
                                  f"Structure '{structure.name}' is already added as an OAR.")
                return
        
        # Avoid adding a target as an OAR
        for target in self._selected_targets:
            if target.name == structure.name:
                QMessageBox.warning(self, "Structure Already Used", 
                                  f"Structure '{structure.name}' is already added as a target.")
                return
        
        # Add to selected OARs
        self._selected_oars.append(structure)
        
        # Create OAR list item
        oar_widget = QWidget()
        oar_layout = QHBoxLayout()
        oar_widget.setLayout(oar_layout)
        
        # OAR name
        oar_label = QLabel(structure.name)
        oar_layout.addWidget(oar_label)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedWidth(70)
        remove_btn.clicked.connect(lambda: self._removeOAR(structure, oar_widget))
        oar_layout.addWidget(remove_btn)
        
        # Add to the OARs list
        self._oars_list_layout.addWidget(oar_widget)
    
    def _removeOAR(self, structure, widget):
        """Remove an OAR from the selected OARs list"""
        # Remove from selected OARs
        self._selected_oars = [o for o in self._selected_oars if o.name != structure.name]
        
        # Remove from UI
        widget.setParent(None)
        widget.deleteLater()
    
    def _updateCreatePlanButtonState(self):
        """Update the state of the create plan button based on selections"""
        has_targets = len(self._selected_targets) > 0
        has_current_patient = self._viewController.currentPatient is not None
        has_ct = False
        
        if has_current_patient:
            ct_list = self._viewController.currentPatient.dataDict.get('CTs', [])
            has_ct = len(ct_list) > 0
        
        self._create_plan_btn.setEnabled(has_targets and has_ct)
    
    def _onSelectedImageChanged(self, image):
        """Handler for selected image changes"""
        if isinstance(image, CTImage):
            # Update structures when CT changes
            self._updateStructuresCombos()
    
    def _onCreatePlan(self):
        """Create a new treatment plan"""
        if not self._selected_technique or not self._selected_targets:
            return
        
        # Get current patient and CT
        patient = self._viewController.currentPatient
        if not patient:
            QMessageBox.warning(self, "No Patient", "No patient is selected.")
            return
        
        ct_list = patient.dataDict.get('CTs', [])
        if not ct_list:
            QMessageBox.warning(self, "No CT", "No CT is available for planning.")
            return
        
        # Use the first CT for planning
        ct = ct_list[0]
        
        # Collect prescriptions
        prescriptions = []
        for target in self._selected_targets:
            if target.name in self._prescriptions:
                prescription = self._prescriptions[target.name].value()
                prescriptions.append(prescription)
            else:
                # Default prescription if not set
                prescriptions.append(2.0)
        
        # Apply technique settings
        technique = self._selected_technique
        technique_name = self._technique_combo.currentText()
        
        # Apply common settings
        fractions = self._fractions_spin.value()
        
        # Apply technique-specific settings
        if technique_name == "3DCRT":
            technique.num_beams = self._beams_spin.value()
            technique.beam_energy = float(self._energy_combo.currentText())
        elif technique_name == "VMAT":
            technique.num_arcs = self._arcs_spin.value()
            technique.beam_energy = float(self._energy_combo.currentText())
            technique.control_points_per_arc = self._cp_spin.value()
        elif technique_name == "SRS":
            technique.num_arcs = self._arcs_spin.value()
            technique.beam_energy = float(self._energy_combo.currentText())
            
            # Setup non-coplanar beams if checked
            if self._noncoplanar_check.isChecked():
                # Simple couch angles for non-coplanar setup
                if technique.num_arcs == 1:
                    technique.couch_angles = [0]
                elif technique.num_arcs == 2:
                    technique.couch_angles = [0, 90]
                elif technique.num_arcs == 3:
                    technique.couch_angles = [0, 45, 315]
                else:
                    # Distribute angles around patient
                    step = 360 / technique.num_arcs
                    technique.couch_angles = [i * step for i in range(technique.num_arcs)]
            else:
                # Reset to coplanar
                technique.couch_angles = [0] * technique.num_arcs
                
        elif technique_name == "SBRT":
            technique.num_fractions = self._sbrt_fractions_spin.value()
            technique.num_arcs = self._arcs_spin.value()
            technique.beam_energy = float(self._energy_combo.currentText())
            
            # Setup non-coplanar beams if checked
            if self._noncoplanar_check.isChecked():
                # Simple couch angles for non-coplanar setup
                if technique.num_arcs == 1:
                    technique.couch_angles = [0]
                elif technique.num_arcs == 2:
                    technique.couch_angles = [0, 90]
                elif technique.num_arcs == 3:
                    technique.couch_angles = [0, 45, 315]
                else:
                    # Distribute angles around patient
                    step = 360 / technique.num_arcs
                    technique.couch_angles = [i * step for i in range(technique.num_arcs)]
            else:
                # Reset to coplanar
                technique.couch_angles = [0] * technique.num_arcs
        
        try:
            # Create the plan
            plan = technique.createPlan(ct, self._selected_targets, 
                                      self._selected_oars, prescriptions)
            
            # Set fractions
            plan.numberOfFractionsPlanned = fractions
            
            # Set plan name
            plan.name = self._plan_name_edit.text()
            
            # Add plan to patient
            patient.addRTPlan(plan)
            
            # Display plan in viewer
            self._viewController.plan = plan
            
            # Enable optimization and dose calculation
            self._optimize_plan_btn.setEnabled(True)
            self._calculate_dose_btn.setEnabled(True)
            
            QMessageBox.information(self, "Plan Created", 
                                  f"Plan '{plan.name}' has been created successfully.")
            
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error creating plan: {str(e)}")
    
    def _onOptimizePlan(self):
        """Optimize the current plan"""
        if not self._selected_technique:
            return
        
        plan = self._viewController.plan
        if not plan:
            QMessageBox.warning(self, "No Plan", "No plan is available for optimization.")
            return
        
        try:
            # Optimize the plan
            plan = self._selected_technique.optimizePlan(plan)
            
            QMessageBox.information(self, "Plan Optimized", 
                                  f"Plan '{plan.name}' has been optimized successfully.")
            
        except Exception as e:
            logger.error(f"Error optimizing plan: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error optimizing plan: {str(e)}")
    
    def _onCalculateDose(self):
        """Calculate dose for the current plan"""
        if not self._selected_technique:
            return
        
        plan = self._viewController.plan
        if not plan:
            QMessageBox.warning(self, "No Plan", "No plan is available for dose calculation.")
            return
        
        # Get current patient and CT
        patient = self._viewController.currentPatient
        if not patient:
            QMessageBox.warning(self, "No Patient", "No patient is selected.")
            return
        
        ct_list = patient.dataDict.get('CTs', [])
        if not ct_list:
            QMessageBox.warning(self, "No CT", "No CT is available for dose calculation.")
            return
        
        # Use the first CT for dose calculation
        ct = ct_list[0]
        
        try:
            # Calculate dose
            dose = self._selected_technique.calculateDose(plan, ct)
            
            # Add dose to patient
            patient.addDoseImage(dose)
            
            # Display dose in viewer
            self._viewController.dose1 = dose
            
            QMessageBox.information(self, "Dose Calculated", 
                                  "Dose has been calculated successfully.")
            
        except Exception as e:
            logger.error(f"Error calculating dose: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error calculating dose: {str(e)}")
    
    def _onPlanCreated(self, plan):
        """Handler for when a plan is created"""
        # Handle plan creation events if needed
        pass
    
    def _onPlanUpdated(self, plan):
        """Handler for when a plan is updated"""
        # Handle plan update events if needed
        pass
    
    def _onComputationProgress(self, progress):
        """Handler for computation progress updates"""
        # Could update a progress bar here if needed
        pass
    
    def showEvent(self, event):
        """Called when the panel becomes visible"""
        super().showEvent(event)
        self._updateStructuresCombos()
        self._updateTechniqueParameters() 