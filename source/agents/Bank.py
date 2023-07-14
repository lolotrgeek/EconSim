from AgentProcess import Agent


class Bank():
    """
    Holds and moves cash and distributes notes to other agents.
    """

    def __init__(self, name, id, initial_balance):
        super().__init__("Bank", id, initial_balance)
        self.reserve_requirement = 0.1
        self.reserve = 0
        self.deposits = []
        self.loans = 0
        self.treasury_notes = 0
        self.treasury_note_face_value = 0
        self.treasury_note_maturity = 0
        self.treasury_note_quantity = 0
        self.treasury_note_interest_rate = 0
        self.treasury_note_interest_payment = 0
        self.treasury_note_principal_payment = 0


        

    