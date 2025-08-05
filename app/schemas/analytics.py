"""
Analytics schemas for account and transaction data visualization.

This module defines the Pydantic schemas for analytics data returned by the API,
including balance history, spending analysis, cash flow, and other financial analytics.
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .base import BaseSchema


class AnalyticsTimeRange(str, Enum):
    """Time range options for analytics endpoints.
    
    Attributes:
        LAST_7_DAYS: Data from the last 7 days
        LAST_30_DAYS: Data from the last 30 days
        LAST_90_DAYS: Data from the last 90 days
        LAST_180_DAYS: Data from the last 180 days
        LAST_YEAR: Data from the last 365 days
        YEAR_TO_DATE: Data from January 1st of the current year
        ALL_TIME: All available historical data
    """
    LAST_7_DAYS = 7
    LAST_30_DAYS = 30
    LAST_90_DAYS = 90
    LAST_180_DAYS = 180
    LAST_YEAR = 365
    YEAR_TO_DATE = "ytd"
    ALL_TIME = "all"


class AnalyticsTimeInterval(str, Enum):
    """Time interval options for data points in analytics responses.
    
    Attributes:
        DAILY: One data point per day
        WEEKLY: One data point per week
        MONTHLY: One data point per month
        QUARTERLY: One data point per quarter
    """
    DAILY = "day"
    WEEKLY = "week"
    MONTHLY = "month"
    QUARTERLY = "quarter"


class BalanceHistoryDataPoint(BaseModel):
    """Data point for balance history timeline.
    
    Attributes:
        date: The date of the balance snapshot
        balance: The account balance on that date
        average_balance: The average balance over the interval ending on this date (optional)
        min_balance: The minimum balance during the interval (optional)
        max_balance: The maximum balance during the interval (optional)
    """
    date: datetime = Field(..., description="Date of the balance snapshot")
    balance: float = Field(..., description="Account balance on this date")
    average_balance: Optional[float] = Field(None, description="Average balance over the interval")
    min_balance: Optional[float] = Field(None, description="Minimum balance during the interval")
    max_balance: Optional[float] = Field(None, description="Maximum balance during the interval")


class BalanceHistoryResponse(BaseSchema):
    """Response model for account balance history.
    
    Attributes:
        account_id: ID of the account
        time_range: The time range of the data
        interval: The time interval between data points
        data: List of balance history data points
        summary: Optional summary statistics
    """
    account_id: int = Field(..., description="ID of the account")
    time_range: AnalyticsTimeRange = Field(..., description="Time range of the data")
    interval: AnalyticsTimeInterval = Field(..., description="Time interval between data points")
    data: List[BalanceHistoryDataPoint] = Field(..., description="Balance history data points")
    summary: Optional[Dict[str, Any]] = Field(None, description="Summary statistics")


class CategorySpending(BaseModel):
    """Spending data for a specific category.
    
    Attributes:
        category: The transaction category
        amount: Total amount spent in this category
        transaction_count: Number of transactions in this category
        percentage: Percentage of total spending in this category
    """
    category: str = Field(..., description="Transaction category")
    amount: float = Field(..., description="Total amount spent")
    transaction_count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total spending")


class SpendingByCategoryResponse(BaseSchema):
    """Response model for spending by category analysis.
    
    Attributes:
        account_id: ID of the account
        time_range: The time range of the data
        data: List of spending by category
        total_spending: Total spending across all categories
    """
    account_id: int = Field(..., description="ID of the account")
    time_range: AnalyticsTimeRange = Field(..., description="Time range of the data")
    data: List[CategorySpending] = Field(..., description="Spending by category")
    total_spending: float = Field(..., description="Total spending across all categories")


class CashFlowDataPoint(BaseModel):
    """Data point for cash flow analysis.
    
    Attributes:
        date: The date of the cash flow snapshot
        inflow: Total money coming into the account
        outflow: Total money going out of the account
        net_flow: Net cash flow (inflow - outflow)
        running_balance: Running account balance
    """
    date: datetime = Field(..., description="Date of the cash flow snapshot")
    inflow: float = Field(..., description="Total money coming in")
    outflow: float = Field(..., description="Total money going out")
    net_flow: float = Field(..., description="Net cash flow (inflow - outflow)")
    running_balance: float = Field(..., description="Running account balance")


class CashFlowResponse(BaseSchema):
    """Response model for cash flow analysis.
    
    Attributes:
        account_id: ID of the account
        time_range: The time range of the data
        data: List of cash flow data points
        summary: Summary of cash flow statistics
    """
    account_id: int = Field(..., description="ID of the account")
    time_range: AnalyticsTimeRange = Field(..., description="Time range of the data")
    data: List[CashFlowDataPoint] = Field(..., description="Cash flow data points")
    summary: Dict[str, Any] = Field(..., description="Cash flow summary statistics")
