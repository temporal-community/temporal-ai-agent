using System.Text.Json.Serialization;

namespace TrainSearchWorker.Models;

public record Journey
{
    [JsonPropertyName("id")]
    public required string Id { get; init; }

    [JsonPropertyName("type")]
    public required string Type { get; init; }

    [JsonPropertyName("departure")]
    public required string Departure { get; init; }

    [JsonPropertyName("arrival")]
    public required string Arrival { get; init; }

    [JsonPropertyName("departure_time")]
    public required string DepartureTime { get; init; }

    [JsonPropertyName("arrival_time")]
    public required string ArrivalTime { get; init; }

    [JsonPropertyName("price")]
    public required decimal Price { get; init; }
}