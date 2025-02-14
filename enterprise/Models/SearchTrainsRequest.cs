namespace TrainSearchWorker.Models;

public record SearchTrainsRequest
{
    public required string From { get; init; }
    public required string To { get; init; }
    public required string OutboundTime { get; init; }
    public required string ReturnTime { get; init; }
}
