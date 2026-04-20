import enum


class MaritalStatus(enum.Enum):
    single = "single"
    married = "married"


class AccountType(enum.Enum):
    retirement = "retirement"
    non_retirement = "non_retirement"
    trust = "trust"


class SubType(enum.Enum):
    # Retirement
    IRA = "IRA"
    Roth_IRA = "Roth IRA"
    K401 = "401K"
    Pension = "Pension"
    # Non-Retirement
    Brokerage = "Brokerage"
    Joint = "Joint"
    # Trust
    Property = "Property"


class Owner(enum.Enum):
    client1 = "client1"
    client2 = "client2"
    joint = "joint"


class LiabilityType(enum.Enum):
    Mortgage = "Mortgage"
    Auto_Loan = "Auto Loan"
    Student_Loan = "Student Loan"
    Other = "Other"


class ProfileRole(enum.Enum):
    primary = "primary"
    spouse = "spouse"


# Validation: which sub_types belong to which account_type
VALID_SUB_TYPES = {
    AccountType.retirement: [SubType.IRA, SubType.Roth_IRA, SubType.K401, SubType.Pension],
    AccountType.non_retirement: [SubType.Brokerage, SubType.Joint],
    AccountType.trust: [SubType.Property],
}
