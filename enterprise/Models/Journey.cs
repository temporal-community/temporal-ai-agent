namespace TrainSearchWorker.Models;

public record Journey
{
    public required string Id { get; init; }
    public required string Type { get; init; }
    public required string Departure { get; init; }
    public required string Arrival { get; init; }
    public required string DepartureTime { get; init; }
    public required string ArrivalTime { get; init; }
    public required decimal Price { get; init; }
}
