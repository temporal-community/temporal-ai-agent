using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace TrainSearchWorker.Models;

public record BookTrainsResponse
{
    [JsonPropertyName("booking_reference")]
    public required string BookingReference { get; init; }
    
    // If the API now returns train_ids as an array, use List<string>
    [JsonPropertyName("train_ids")]
    public required List<string> TrainIds { get; init; }
    
    [JsonPropertyName("status")]
    public required string Status { get; init; }
}
