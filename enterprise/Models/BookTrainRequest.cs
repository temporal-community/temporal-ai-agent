namespace TrainSearchWorker.Models;

public record BookTrainsRequest
{
    public required string TrainIds { get; init; }
}
