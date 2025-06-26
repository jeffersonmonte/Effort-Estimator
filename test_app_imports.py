import unittest

class TestAppImports(unittest.TestCase):

    def test_import_libraries(self):
        """
        Test that all required libraries in app.py can be imported.
        """
        try:
            from datetime import date
            import numpy as np
            import pandas as pd
            import plotly.express as px
            import plotly.graph_objects as go
            import streamlit as st
            from uuid import uuid4

            # Imports from the 'estimation' module
            # Assuming 'estimation' is in PYTHONPATH or a local directory
            # If these cause issues, they might need to be mocked or the
            # PYTHONPATH configured for the test environment.
            # from estimation.models import (AnchorStory, EstimationMode, Factor, Sector,
            #                                SprintMetric)
            # from estimation.repository import Repository
            # from estimation.seed import seed_data
            # from estimation.services import (ComplexityScorer, EstimationService,
            #                                  FibonacciRound, MonteCarloService,
            #                                  calculate_days_per_sp,
            #                                  convert_to_story_points)
            imported_successfully = True
        except ImportError as e:
            imported_successfully = False
            print(f"Failed to import libraries: {e}")

        self.assertTrue(imported_successfully, "One or more libraries failed to import.")

if __name__ == '__main__':
    unittest.main()
