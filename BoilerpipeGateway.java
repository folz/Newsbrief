import py4j.GatewayServer;

import java.net.URL;

import de.l3s.boilerpipe.extractors.ArticleExtractor;

import net.sf.classifier4J.summariser.*;

class BoilerpipeGateway {

    public BoilerpipeGateway() {}

    public String getText(String urlstr) throws Exception {
        URL url = new URL(urlstr);
        return ArticleExtractor.INSTANCE.getText(url);
    }

    public String getSummary(String text, int sentences) {
        ISummariser s = new SimpleSummariser();
        return s.summarise(text, sentences);
    }

    public static void main(String[] args) throws Exception {
        GatewayServer gatewayServer = new GatewayServer(new BoilerpipeGateway());
        gatewayServer.start();
        System.out.println("Gateway server started");
    }
}
