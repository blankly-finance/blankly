import Blankly
import time
from bokeh.plotting import figure, output_file, show

if __name__ == "__main__":
    output_file('line.html')
    market = 'BTC-USD'
    p = figure(plot_width=800, plot_height=900)
    # Construct our authenticated exchange
    portfolio = Blankly.CoinbasePro()
    # Get the interface for API calls
    interface = portfolio.get_interface()

    # Download market data
    print("Downloading...")
    history = interface.get_product_history(market, time.time() - Blankly.time_builder.build_day() * 300, time.time(),
                                            Blankly.time_builder.build_day())
    # Create X-axis
    x = range(len(history['close']))

    # Shift the graph to match
    shift = [shift + 99 for shift in x]
    # Plot 100 day moving average
    p.line(shift, Blankly.indicators.sma(history["close"], 100), line_width=2, line_color='pink',
           legend_label="100d SMA")

    # Shift the graph to match
    shift = [shift+49 for shift in x]
    # Plot 50 day moving average
    p.line(shift, Blankly.indicators.sma(history["close"], 50), line_width=2, line_color='yellow',
           legend_label="50d SMA")

    # Plot close price
    p.line(x, history["close"], line_width=2)

    # Format graph
    p.legend.location = "top_left"
    p.legend.title = market
    p.legend.title_text_font_style = "bold"
    p.legend.title_text_font_size = "20px"
    show(p)
