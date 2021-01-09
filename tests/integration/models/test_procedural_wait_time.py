from models.procedural_wait_time import ProceduralWaitTimeModel
from tests.base_test import BaseTest


class ProceduralWaitTimeModelTest(BaseTest):
    def test_crud(self):
        with self.app_context():
            procedure = "High 5"
            wait_time = "12"

            procedural_wait_time = ProceduralWaitTimeModel(procedure=procedure,
                                                           wait_time=wait_time)

            self.assertIsNone(ProceduralWaitTimeModel.find_by_id(
                1), "Found a procedural wait time with id '1' before save_to_db")

            procedural_wait_time.save_to_db()

            self.assertIsNotNone(ProceduralWaitTimeModel.find_by_id(
                1), "Did not find a procedural wait time with id '1' after save_to_db")
