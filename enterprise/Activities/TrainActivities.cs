using System.Net.Http.Json;
using Temporalio.Activities;
using TrainSearchWorker.Models;

namespace TrainSearchWorker.Activities;

public class TrainActivities
{
    private readonly HttpClient _client;

    public TrainActivities(IHttpClientFactory clientFactory)
    {
        _client = clientFactory.CreateClient("TrainApi");
    }

    [Activity]
    public async Task<List<Journey>> SearchTrains(SearchTrainsRequest request)
    {
        var response = await _client.GetAsync(
            $"api/search?from={Uri.EscapeDataString(request.From)}" +
            $"&to={Uri.EscapeDataString(request.To)}" +
            $"&outbound_time={Uri.EscapeDataString(request.OutboundTime)}" +
            $"&return_time={Uri.EscapeDataString(request.ReturnTime)}");

        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<List<Journey>>() 
            ?? throw new InvalidOperationException("Received null response from API");
    }

    [Activity]
    public async Task<List<Journey>> BookTrains(BookTrainsRequest request)
    {
        var response = await _client.PostAsJsonAsync("api/book", request);
        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<List<Journey>>()
            ?? throw new InvalidOperationException("Received null response from API");
    }
}
