using System.Text.Json.Serialization;

namespace TrainSearchWorker.Models;

public record BookTrainsRequest
{
    [JsonPropertyName("train_ids")]
    public required string TrainIds { get; init; }
}
