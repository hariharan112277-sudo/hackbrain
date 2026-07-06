"""
IOB Phase 4 Pipeline Exception Registry
Standard Compliance: ISA-95 Part 2, IEC 62443 Edge Processing Software Component.
"""

class IngestionPipelineException(Exception):
    """Root pipeline execution error."""
    pass

class MalformedJsonException(IngestionPipelineException):
    """Payload fails basic structural JSON parsing."""
    pass

class SchemaValidationException(IngestionPipelineException):
    """Payload deviates from the defined structural schema."""
    pass

class ClockDriftViolationException(IngestionPipelineException):
    """Timestamp drift exceeds configured operational limits."""
    pass

class DuplicatePacketException(IngestionPipelineException):
    """Identical packet signature found within sliding window cache."""
    pass

class UnitConversionException(IngestionPipelineException):
    """Error converting engineering unit scales."""
    pass


# Backwards compatibility aliases
IngestionException = IngestionPipelineException
PayloadValidationException = IngestionPipelineException
TimestampValidationException = ClockDriftViolationException
DuplicatePayloadException = DuplicatePacketException
QualityCheckException = IngestionPipelineException
NormalizationException = UnitConversionException
EnrichmentException = IngestionPipelineException
ParseException = IngestionPipelineException
DispatchException = IngestionPipelineException
RetryExhaustedException = IngestionPipelineException
