using Microsoft.Extensions.DependencyInjection;
using Temporalio.Client;
using Temporalio.Worker;
using TrainSearchWorker.Activities;

var services = new ServiceCollection();

// Add HTTP client
services.AddHttpClient("TrainApi", client =>
{
    client.BaseAddress = new Uri("http://localhost:8080/");
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// Add activities
services.AddScoped<TrainActivities>();

var serviceProvider = services.BuildServiceProvider();

// Create client
var client = await TemporalClient.ConnectAsync(new()
{
    TargetHost = "localhost:7233",
});

// Create worker options
var options = new TemporalWorkerOptions("agent-task-queue-legacy");

// Register activities
var activities = serviceProvider.GetRequiredService<TrainActivities>();
options.AddActivity(activities.SearchTrains);
options.AddActivity(activities.BookTrains);

// Create and run worker
var worker = new TemporalWorker(client, options);

Console.WriteLine("Starting worker...");
using var tokenSource = new CancellationTokenSource();
Console.CancelKeyPress += (_, eventArgs) =>
{
    eventArgs.Cancel = true;
    tokenSource.Cancel();
};

try 
{
    await worker.ExecuteAsync(tokenSource.Token);
}
catch (OperationCanceledException)
{
    Console.WriteLine("Worker shutting down...");
}