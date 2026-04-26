import { Mail } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs'
import { SectionLabel } from './RequirementsCard'
import type { Communications } from '../types/api'

interface Props {
  communications: Communications
}

export function CommunicationsSection({ communications }: Props) {
  return (
    <section>
      <SectionLabel icon={Mail} label="Communications" step={4} />
      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="invitation">
            <TabsList className="mb-4 flex-wrap">
              <TabsTrigger value="invitation">Invitation Email</TabsTrigger>
              <TabsTrigger value="vendor">Vendor Brief</TabsTrigger>
              <TabsTrigger value="plan">Full Event Plan</TabsTrigger>
            </TabsList>

            <TabsContent value="invitation">
              <DocumentView content={communications.invitation_email} />
            </TabsContent>
            <TabsContent value="vendor">
              <DocumentView content={communications.vendor_brief} />
            </TabsContent>
            <TabsContent value="plan">
              <DocumentView content={communications.final_plan} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </section>
  )
}

function DocumentView({ content }: { content: string }) {
  return (
    <div className="rounded-[10px] bg-[#F5F5F7] p-5">
      <pre
        className="whitespace-pre-wrap font-[inherit] text-[13px] leading-relaxed text-[#1D1D1F]"
        style={{ fontFamily: 'inherit' }}
      >
        {content}
      </pre>
    </div>
  )
}
