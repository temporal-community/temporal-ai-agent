using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace TrainSearchWorker.Models;

public record JourneyResponse
{
    [JsonPropertyName("journeys")]
    public List<Journey>? Journeys { get; init; }
}
