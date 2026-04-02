"""Sub-agent implementations for the multi-agent task manager."""

from task_manager.agents.task_manager_agent import TaskManagerSubAgent
from task_manager.agents.calendar_agent import CalendarSubAgent
from task_manager.agents.notes_agent import NotesSubAgent
from task_manager.agents.appointment_agent import AppointmentSubAgent
from task_manager.agents.pathology_agent import PathologySubAgent
from task_manager.agents.medication_agent import MedicationSubAgent
from task_manager.agents.nurse_agent import NurseSubAgent
from task_manager.agents.reminder_agent import ReminderSubAgent
from task_manager.agents.cost_guard_agent import CostGuardSubAgent

__all__ = [
    "TaskManagerSubAgent",
    "CalendarSubAgent",
    "NotesSubAgent",
    "AppointmentSubAgent",
    "PathologySubAgent",
    "MedicationSubAgent",
    "NurseSubAgent",
    "ReminderSubAgent",
    "CostGuardSubAgent",
]
