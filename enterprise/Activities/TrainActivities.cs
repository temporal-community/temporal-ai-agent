using System.Net.Http.Json;
using System.Text.Json;
using Temporalio.Activities;
using TrainSearchWorker.Models;
using Microsoft.Extensions.Logging;

namespace TrainSearchWorker.Activities;

public class TrainActivities
{
    private readonly HttpClient _client;
    private readonly JsonSerializerOptions _jsonOptions;

    public TrainActivities(IHttpClientFactory clientFactory)
    {
        _client = clientFactory.CreateClient("TrainApi");
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        };
    }


    [Activity]
    public async Task<JourneyResponse> SearchTrains(SearchTrainsRequest request)
    {
        ActivityExecutionContext.Current.Logger.LogInformation($"SearchTrains from {request.From} to {request.To}");
        var response = await _client.GetAsync(
            $"api/search?from={Uri.EscapeDataString(request.From)}" +
            $"&to={Uri.EscapeDataString(request.To)}" +
            $"&outbound_time={Uri.EscapeDataString(request.OutboundTime)}" +
            $"&return_time={Uri.EscapeDataString(request.ReturnTime)}");

        response.EnsureSuccessStatusCode();
      
        // Deserialize into JourneyResponse rather than List<Journey>
        var journeyResponse = await response.Content.ReadFromJsonAsync<JourneyResponse>(_jsonOptions)
                              ?? throw new InvalidOperationException("Received null response from API");

        ActivityExecutionContext.Current.Logger.LogInformation("SearchTrains completed");

        return journeyResponse;
    }

    [Activity]
    public async Task<BookTrainsResponse> BookTrains(BookTrainsRequest request)
    {
        ActivityExecutionContext.Current.Logger.LogInformation($"Booking trains with IDs: {request.TrainIds}");

        // Build the URL using the train IDs from the request
        var url = $"api/book/{Uri.EscapeDataString(request.TrainIds)}";

        // POST with no JSON body, matching the Python version
        var response = await _client.PostAsync(url, null);
        response.EnsureSuccessStatusCode();

        // Deserialize into a BookTrainsResponse (a single object)
        var bookingResponse = await response.Content.ReadFromJsonAsync<BookTrainsResponse>(_jsonOptions)
                              ?? throw new InvalidOperationException("Received null response from API");

        ActivityExecutionContext.Current.Logger.LogInformation("BookTrains completed");

        return bookingResponse;
    }

}
