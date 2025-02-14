using System.Text.Json.Serialization;

namespace TrainSearchWorker.Models;

public record SearchTrainsRequest
{
    [JsonPropertyName("origin")]
    public required string From { get; init; }

    [JsonPropertyName("destination")]
    public required string To { get; init; }

    [JsonPropertyName("outbound_time")]
    public required string OutboundTime { get; init; }

    [JsonPropertyName("return_time")]
    public required string ReturnTime { get; init; }
}
