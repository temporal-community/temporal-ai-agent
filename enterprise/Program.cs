using Microsoft.Extensions.DependencyInjection;
using Temporalio.Client;
using Temporalio.Worker;
using TrainSearchWorker.Activities;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Console;

// Set up dependency injection
var services = new ServiceCollection();

var loggerFactory = LoggerFactory.Create(builder =>
{
    builder
        .AddSimpleConsole(options => options.TimestampFormat = "[HH:mm:ss] ")
        .SetMinimumLevel(LogLevel.Information);
});

// Add HTTP client
services.AddHttpClient("TrainApi", client =>
{
    client.BaseAddress = new Uri("http://localhost:8080/");
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

// Add activities
services.AddScoped<TrainActivities>();

var serviceProvider = services.BuildServiceProvider();

// Create client using the helper, which supports Temporal Cloud if environment variables are set
var client = await TemporalClientHelper.CreateClientAsync();

// Read connection details from environment or use defaults
var address = Environment.GetEnvironmentVariable("TEMPORAL_ADDRESS") ?? "localhost:7233";
var ns = Environment.GetEnvironmentVariable("TEMPORAL_NAMESPACE") ?? "default";

// Log connection details
Console.WriteLine("Starting worker...");
Console.WriteLine($"Connecting to Temporal at address: {address}");
Console.WriteLine($"Using namespace: {ns}");

// Create worker options
var options = new TemporalWorkerOptions("agent-task-queue-legacy")
{
    LoggerFactory = loggerFactory
};

// Register activities
var activities = serviceProvider.GetRequiredService<TrainActivities>();
options.AddActivity(activities.SearchTrains);
options.AddActivity(activities.BookTrains);

// Create and run worker
var worker = new TemporalWorker(client, options);

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
